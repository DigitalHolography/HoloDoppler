"""Benchmark preview/process calls with external resource sampling and a PDF report.

Examples (run from the repository root):
    python scripts/benchmark_pipeline.py recording.holo -p parameters/default_parameters_default.yaml
    python scripts/benchmark_pipeline.py recording.holo -p params.yaml --pipeline default --end-frame 2048
    python scripts/benchmark_pipeline.py recording.holo -p params.yaml --mode process --backend numpy

Install the optional CPU-monitoring dependency with: pip install -e '.[benchmark]'
NVIDIA monitoring uses nvidia-smi if available; missing GPU metrics remain unavailable.
"""
from __future__ import annotations

import argparse
from collections import deque
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import textwrap
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MIB = 1024**2
CPU_FIELDS = ('time_s', 'stage', 'pid', 'rss_mib', 'process_cpu_percent',
              'system_cpu_percent', 'system_used_mib', 'system_available_mib', 'processes')
GPU_FIELDS = ('time_s', 'stage', 'uuid', 'index', 'name', 'vram_used_mib',
              'vram_total_mib', 'process_vram_mib', 'gpu_percent', 'memory_percent')


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + '\n', encoding='utf-8')


def _event(path, kind, **fields):
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(dict(event=kind, monotonic=time.perf_counter(), **fields), default=str) + '\n')


def _worker(config_path, stage):
    """Run one real API call. CUDA state and imports never enter the monitor."""
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    directory = Path(config['directory'])
    events = directory / f'{stage}.events.jsonl'
    _event(events, 'worker_start', pid=os.getpid())
    params = dict(config['parameters'])
    params['custom_path'] = str(directory / f'{stage}-output')
    status, error, start = 'failed', None, None
    try:
        from holodoppler.logging import configure_logging, logger
        configure_logging(log_path=directory / f'{stage}.application.log')
        from holodoppler.config import load_config
        params = load_config(params)
        from holodoppler import backend
        from holodoppler.cli import preview, process
        if config['backend'] is not None:
            backend.set_backend(config['backend'])
            params['force_numpy'] = config['backend'] == 'numpy'
        elif params.get('force_numpy', False):
            backend.set_backend('numpy')
        _event(events, 'ready', backend=backend.get_backend_name())
        _write_json(directory / f'{stage}.parameters.json', params)

        def progress(completed, total, message):
            _event(events, 'progress', completed=int(completed), total=int(total), message=message)

        def warning(title, message):
            logger.warning('%s: %s', title, message)

        start = time.perf_counter()
        _event(events, 'call_start', backend=backend.get_backend_name())
        if stage == 'preview':
            result = preview(Path(config['file']), params)
        else:
            result = process(Path(config['file']), params, progress_callback=progress,
                             warning_callback=warning)
        # Include outstanding device work, while keeping the returned preview alive.
        backend.synchronize()
        _event(events, 'result', result_type=type(result).__name__)
        status = 'success'
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        traceback.print_exc()
    finally:
        end = time.perf_counter()
        _event(events, 'call_end', status=status, error=error,
               seconds=None if start is None else end - start)
        _write_json(directory / f'{stage}.parameters.json', params)
    return 0 if status == 'success' else 1


class ProcessSampler:
    """Sample the worker and live descendants; 100% CPU means one logical core."""
    def __init__(self, pid, psutil):
        self.psutil = psutil
        self.root = psutil.Process(pid)
        self.previous = {}
        self.known_children = {}
        self.previous_time = time.perf_counter()
        psutil.cpu_percent(interval=None)

    def sample(self):
        now = time.perf_counter()
        try:
            processes = [self.root, *self.root.children(recursive=True)]
        except self.psutil.Error:
            processes = []
        current, pids, rss, cpu_delta = {}, set(), 0, 0.
        for process in processes:
            try:
                with process.oneshot():
                    key = (process.pid, process.create_time())
                    times = process.cpu_times()
                    cpu = times.user + times.system
                    rss += process.memory_info().rss
                    current[key] = cpu
                    pids.add(process.pid)
                    if process.pid != self.root.pid:
                        self.known_children[key] = process
                    if key in self.previous:
                        cpu_delta += max(0., cpu - self.previous[key])
            except self.psutil.Error:
                continue
        elapsed = now - self.previous_time
        self.previous, self.previous_time = current, now
        memory = self.psutil.virtual_memory()
        return dict(monotonic=now, rss_mib=rss / MIB,
                    process_cpu_percent=100 * cpu_delta / elapsed if elapsed else 0.,
                    system_cpu_percent=self.psutil.cpu_percent(interval=None),
                    system_used_mib=(memory.total - memory.available) / MIB,
                    system_available_mib=memory.available / MIB, processes=len(pids)), pids


def _number(value):
    try:
        result = float(value.strip())
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def _gpu_devices(output):
    devices = []
    for row in csv.reader(output.splitlines(), skipinitialspace=True):
        if len(row) != 7:
            continue
        index, identifier, name, used, total, utilization, memory = row
        devices.append(dict(index=index.strip(), uuid=identifier.strip(), name=name.strip(),
                            vram_used_mib=_number(used), vram_total_mib=_number(total),
                            gpu_percent=_number(utilization), memory_percent=_number(memory)))
    return devices


def _process_vram(output, pids):
    """None is unavailable, distinct from a measured zero for a CPU-only worker."""
    memory = {}
    for row in csv.reader(output.splitlines(), skipinitialspace=True):
        if len(row) != 3:
            continue
        identifier, pid, used = (item.strip() for item in row)
        if not pid.isdigit() or int(pid) not in pids:
            continue
        value = _number(used)
        previous = memory.get(identifier, 0.)
        memory[identifier] = None if value is None or previous is None else previous + value
    return memory


class NvidiaSampler:
    """Poll nvidia-smi asynchronously so slow driver queries do not stall RAM sampling.

    Both queries use tiny pipe outputs. All work runs in this monitor process's
    event loop; no Python sampling threads or locks are needed.
    """
    def __init__(self, interval, timeout):
        self.executable = shutil.which('nvidia-smi')
        self.interval, self.timeout = interval, timeout
        self.pending = None
        self.next_query = 0.
        self.warnings = [] if self.executable else ['nvidia-smi unavailable: GPU/VRAM metrics were not collected.']
        self.disabled = not bool(self.executable)

    def _start(self, kind):
        query = ('index,uuid,name,memory.used,memory.total,utilization.gpu,utilization.memory'
                 if kind == 'gpu' else 'gpu_uuid,pid,used_gpu_memory')
        option = '--query-gpu=' if kind == 'gpu' else '--query-compute-apps='
        self.kind, self.started = kind, time.perf_counter()
        try:
            self.pending = subprocess.Popen(
                [self.executable, option + query, '--format=csv,noheader,nounits'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
        except OSError as exc:
            self.warnings.append(f'NVIDIA monitoring unavailable: {exc}')
            self.disabled = True
            self.pending = None

    def tick(self, pids):
        now = time.perf_counter()
        if self.disabled:
            return None
        if self.pending is None:
            if now >= self.next_query:
                self.pids = set(pids)
                self.observed_at = now
                self._start('gpu')
            return None
        if self.pending.poll() is None:
            if now - self.started <= self.timeout:
                return None
            self.pending.kill()
            self.pending.communicate()
            self.pending = None
            self.disabled = True
            self.warnings.append('NVIDIA query timed out; subsequent GPU metrics are unavailable.')
            return None
        output, error = self.pending.communicate()
        code = self.pending.returncode
        self.pending = None
        if self.kind == 'gpu':
            self.devices = _gpu_devices(output) if code == 0 else []
            if not self.devices:
                self.disabled = True
                self.warnings.append('NVIDIA GPU metrics unavailable: ' + (error or output).strip()[:500])
                return None
            self._start('process')
            return None
        per_process = _process_vram(output, self.pids) if code == 0 else None
        if code != 0:
            message = 'Per-process VRAM unavailable (device-wide metrics are still collected).'
            if message not in self.warnings:
                self.warnings.append(message)
        for device in self.devices:
            device['process_vram_mib'] = None if per_process is None else per_process.get(device['uuid'], 0.)
        self.next_query = now + self.interval
        return dict(monotonic=self.observed_at, devices=self.devices)

    def close(self):
        if self.pending is not None:
            if self.pending.poll() is None:
                self.pending.kill()
            self.pending.communicate()
            self.pending = None


def _read_events(path):
    events = []
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # A forcibly killed worker can leave a partial final line.
    return events


def _run_stage(config_path, stage, directory, args, psutil):
    log_path = directory / f'{stage}.log'
    origin = time.perf_counter()
    cpu, gpu = [], []
    monitor = NvidiaSampler(args.gpu_interval, args.gpu_timeout)
    interrupted, timed_out = False, False
    with log_path.open('w', encoding='utf-8') as log:
        environment = os.environ.copy()
        environment.update(PYTHONUNBUFFERED='1', MPLBACKEND='Agg',
                           MPLCONFIGDIR=str(directory / 'matplotlib'))
        worker = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_worker',
                                   str(config_path), stage], stdout=log, stderr=subprocess.STDOUT,
                                  cwd=ROOT, env=environment)
        sampler = ProcessSampler(worker.pid, psutil)
        next_cpu, pids = origin, {worker.pid}
        try:
            while worker.poll() is None:
                now = time.perf_counter()
                if now >= next_cpu:
                    sample, pids = sampler.sample()
                    sample['time_s'] = sample.pop('monotonic') - origin
                    sample.update(stage=stage, pid=worker.pid)
                    cpu.append(sample)
                    next_cpu = now + args.interval
                observation = monitor.tick(pids)
                if observation is not None:
                    observation['time_s'] = observation.pop('monotonic') - origin
                    gpu.append(observation)
                if args.timeout is not None and time.perf_counter() - origin > args.timeout:
                    timed_out = True
                    break
                # Poll GPU subprocess completion promptly, independently of its cadence.
                time.sleep(min(.05, max(0., next_cpu - time.perf_counter())))
        except KeyboardInterrupt:
            interrupted = True
        finally:
            if worker.poll() is None or worker.returncode != 0:
                descendants = dict(sampler.known_children)
                try:
                    for process in psutil.Process(worker.pid).children(recursive=True):
                        descendants[(process.pid, process.create_time())] = process
                except psutil.Error:
                    pass
                for process in reversed(list(descendants.values())):
                    try:
                        process.terminate()
                    except psutil.Error:
                        pass
                if worker.poll() is None:
                    worker.terminate()
                    try:
                        worker.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        worker.kill()
                        worker.wait()
                _, alive = psutil.wait_procs(list(descendants.values()), timeout=2)
                for process in alive:
                    try:
                        process.kill()
                    except psutil.Error:
                        pass
            monitor.close()
    elapsed = time.perf_counter() - origin
    events = _read_events(directory / f'{stage}.events.jsonl')
    for event in events:
        event['time_s'] = event['monotonic'] - origin
    start = next((event for event in events if event['event'] == 'call_start'), None)
    end = next((event for event in events if event['event'] == 'call_end'), None)
    ready = next((event for event in events if event['event'] == 'ready'), {})
    status = ('interrupted' if interrupted else 'timeout' if timed_out else
              end['status'] if end is not None and worker.returncode == 0 else 'failed')
    error = None if status == 'success' else ((end or {}).get('error') or
            (f'Worker exceeded --timeout {args.timeout} s' if timed_out else
             'Benchmark interrupted' if interrupted else f'Worker exit code {worker.returncode}'))
    if start is not None:
        bound = end['time_s'] if end is not None else elapsed
        call_cpu = [sample for sample in cpu if start['time_s'] <= sample['time_s'] <= bound]
        call_gpu = [sample for sample in gpu if start['time_s'] <= sample['time_s'] <= bound]
    else:
        call_cpu, call_gpu = [], []
    warnings = list(monitor.warnings)
    if start is not None and not call_cpu:
        warnings.append('No CPU/RAM sample landed inside this short API call. Reduce --interval; sampled peaks may miss spikes.')
    if not call_gpu and not monitor.disabled:
        warnings.append('No complete NVIDIA sample landed inside the API call; GPU peaks are unavailable.')
    def peak(records, key):
        return max((record[key] for record in records if record.get(key) is not None), default=None)
    return dict(stage=stage, pid=worker.pid, status=status, error=error, returncode=worker.returncode,
                backend=ready.get('backend', 'unknown'), worker_wall_seconds=elapsed,
                startup_seconds=None if start is None else start['time_s'],
                call_seconds=(end or {}).get('seconds'), peak_rss_mib=peak(call_cpu, 'rss_mib'),
                peak_process_cpu_percent=peak(call_cpu, 'process_cpu_percent'),
                peak_process_vram_mib=peak([device for item in call_gpu for device in item['devices']], 'process_vram_mib'),
                warnings=warnings, cpu=cpu, gpu=gpu, events=events, log=str(log_path))


def _save_samples(directory, results):
    with (directory / 'cpu.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=CPU_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerows(result['cpu'])
    with (directory / 'gpu.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=GPU_FIELDS)
        writer.writeheader()
        for result in results:
            for observation in result['gpu']:
                for device in observation['devices']:
                    writer.writerow(dict(time_s=observation['time_s'], stage=result['stage'], **device))


def _format(value, suffix=''):
    return 'unavailable' if value is None else f'{value:,.3f}{suffix}'


def _text_pages(pdf, plt, title, lines):
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(str(line), width=145, replace_whitespace=False,
                                     drop_whitespace=False) or [''])
    for offset in range(0, len(wrapped), 48):
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.text(.05, .95, title + (f' (continued, page {offset // 48 + 1})' if offset else ''), fontsize=15, va='top')
        fig.text(.05, .89, '\n'.join(wrapped[offset:offset + 48]), fontsize=8,
                 family='DejaVu Sans Mono', va='top', linespacing=1.25)
        pdf.savefig(fig)
        plt.close(fig)


def _resource_page(pdf, plt, result):
    fig, axes = plt.subplots(2, 2, figsize=(11.7, 8.3), constrained_layout=True)
    ram, cpu, vram, gpu = axes.flat
    samples = result['cpu']
    x = [sample['time_s'] for sample in samples]
    ram.plot(x, [sample['rss_mib'] for sample in samples], label='Worker + live children RSS')
    system_ram = ram.twinx()
    system_ram.plot(x, [sample['system_used_mib'] / 1024 for sample in samples],
                    label='System used (total - available)', color='tab:orange', alpha=.7)
    system_ram.set_ylabel('System RAM (GiB)', color='tab:orange')
    system_ram.tick_params(axis='y', labelcolor='tab:orange')
    cpu.plot(x, [sample['process_cpu_percent'] for sample in samples], label='Worker tree (100% = one core)')
    cpu.plot(x, [sample['system_cpu_percent'] for sample in samples], label='System CPU (0-100%)', alpha=.7)
    ram.set(title='RAM', ylabel='Worker tree RSS (MiB)')
    cpu.set(title='CPU usage', ylabel='%')
    devices = {device['uuid']: device for obs in result['gpu'] for device in obs['devices']}
    for identifier, device in devices.items():
        rows = [(obs['time_s'], item) for obs in result['gpu'] for item in obs['devices'] if item['uuid'] == identifier]
        label = f'GPU {device["index"]}'
        for axis, key, description, style in (
            (vram, 'vram_used_mib', 'device total', '-'),
            (vram, 'process_vram_mib', 'worker tree', '--'),
            (gpu, 'gpu_percent', 'compute utilization', '-'),
            (gpu, 'memory_percent', 'memory-controller utilization', '--'),
        ):
            points = [(when, item[key]) for when, item in rows if item.get(key) is not None]
            if points:
                axis.plot(*zip(*points), label=f'{label}: {description}', linestyle=style, marker='.')
    vram.set(title='VRAM', ylabel='MiB')
    gpu.set(title='GPU usage (device-wide)', ylabel='%')
    if not devices:
        for axis in (vram, gpu):
            axis.text(.5, .5, 'GPU telemetry unavailable', transform=axis.transAxes, ha='center')
    for axis in axes.flat:
        axis.set_xlim(0, max(result['worker_wall_seconds'], .001))
        axis.set_xlabel('Seconds since worker launch (startup included)')
        axis.grid(alpha=.25)
        if axis.get_legend_handles_labels()[0]:
            axis.legend(fontsize=7, loc='upper left')
        for event in result['events']:
            if event['event'] in ('call_start', 'call_end'):
                axis.axvline(event['time_s'], color='tab:purple', linestyle=':', alpha=.7)
    system_ram.legend(fontsize=7, loc='lower right')
    fig.suptitle(f'{result["stage"]}: {result["status"]} | backend: {result["backend"]}\n'
                 'Purple markers bound the API call; GPU timestamps mark query start.', fontsize=13)
    pdf.savefig(fig)
    plt.close(fig)


def _timing_page(pdf, plt, results):
    fig, (calls, batches) = plt.subplots(1, 2, figsize=(11.7, 8.3), constrained_layout=True)
    for index, result in enumerate(results):
        startup = result['startup_seconds']
        duration = result['call_seconds']
        calls.barh(index, startup or 0, label='Startup/imports' if index == 0 else None, color='tab:gray')
        calls.barh(index, duration or 0, left=startup or 0, label='API call incl. saving and GPU sync' if index == 0 else None,
                   color='tab:blue')
        progress = [event for event in result['events'] if event['event'] == 'progress']
        start = next((event for event in result['events'] if event['event'] == 'call_start'), None)
        if progress and start is not None:
            # First interval includes reference preparation; later intervals include
            # ordered consumption, saving/backpressure, and callback overhead.
            boundaries = [start['time_s'], *[event['time_s'] for event in progress]]
            intervals = [b - a for a, b in zip(boundaries, boundaries[1:])]
            batches.plot([event['completed'] for event in progress], intervals, '.-', label=result['stage'])
    calls.set_yticks(range(len(results)), [result['stage'] for result in results])
    calls.set(title='Wall timings', xlabel='Seconds')
    calls.legend(fontsize=8)
    batches.set(title='Intervals between progress callbacks', xlabel='Completed batch', ylabel='Seconds')
    if batches.get_legend_handles_labels()[0]:
        batches.legend()
    else:
        batches.text(.5, .5, 'No batch callbacks recorded', transform=batches.transAxes, ha='center')
    for axis in (calls, batches):
        axis.grid(alpha=.25)
    pdf.savefig(fig)
    plt.close(fig)


def _report(path, manifest, results, log_lines):
    # Report generation happens after workers exit and is excluded from metrics.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(path) as pdf:
        pdf.infodict().update(Title='HoloDoppler pipeline benchmark', Author='HoloDoppler')
        lines = [f'Date: {manifest["created_utc"]}', f'Input: {manifest["file"]}',
                 f'Input size: {manifest["file_size_bytes"]:,} bytes',
                 f'Pipeline: {manifest["parameters"]["pipeline_name"]}',
                 f'Parameters: {manifest["parameters_file"]}',
                 f'end_frame: {manifest["parameters"].get("end_frame", "pipeline default")} (exclusive source-frame bound; file unchanged)',
                 f'System: {manifest["system"]}', f'Python: {manifest["python"]}',
                 f'Logical CPUs: {manifest["logical_cpus"]}; system RAM: {manifest["system_ram_mib"]:,.0f} MiB',
                 f'CPU/RAM interval target: {manifest["interval"]} s; GPU interval target: {manifest["gpu_interval"]} s',
                 f'Artifacts and isolated pipeline outputs: {manifest["directory"]}', '']
        devices = {device['uuid']: device for result in results for observation in result['gpu']
                   for device in observation['devices']}
        for device in devices.values():
            lines.append(f'GPU {device["index"]}: {device["name"]}; VRAM {_format(device["vram_total_mib"], " MiB")}')
        lines.append('')
        for result in results:
            lines += [f'{result["stage"].upper()}: {result["status"]}; actual backend: {result["backend"]}',
                      f'  API wall: {_format(result["call_seconds"], " s")}; startup: {_format(result["startup_seconds"], " s")}; worker wall: {_format(result["worker_wall_seconds"], " s")}',
                      f'  Observed API-call peak RSS: {_format(result["peak_rss_mib"], " MiB")}; CPU: {_format(result["peak_process_cpu_percent"], "%")}',
                      f'  Observed API-call peak worker VRAM per device: {_format(result["peak_process_vram_mib"], " MiB")}']
            if result['error']:
                lines.append('  Error: ' + result['error'])
            lines.extend('  Note: ' + message for message in result['warnings'])
        lines += ['', 'Measurement notes:',
                  '- Each API runs in a fresh process; OS disk caches are not cleared.',
                  '- Calls include reading, calculation, plotting, saving, and final GPU synchronization.',
                  '- Sampled peaks can miss short spikes. RSS sums include shared pages in multiple processes.',
                  '- CPU/RAM cover the worker and live descendants (including encoders), excluding the monitor/report.',
                  '- GPU utilization and total VRAM are device-wide and include other applications.',
                  '- Worker VRAM is NVIDIA compute-process memory, not CuPy pool statistics. N/A stays unavailable.',
                  '- end_frame limits processing batches; preview and reference/autofocus windows retain their configured sizes.',
                  '- Batch callback intervals are not isolated kernel timings, particularly with asynchronous pipelines.']
        _text_pages(pdf, plt, 'HoloDoppler benchmark', lines)
        _timing_page(pdf, plt, results)
        for result in results:
            _resource_page(pdf, plt, result)
        _text_pages(pdf, plt, 'Requested parameters (benchmark overrides applied)',
                    json.dumps(manifest['parameters'], indent=2, default=str).splitlines())
        for result in results:
            with Path(result['log']).open(encoding='utf-8', errors='replace') as handle:
                tail = list(deque(handle, maxlen=log_lines))
            clean = [re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', line).rstrip() for line in tail]
            _text_pages(pdf, plt, f'{result["stage"]} logs (last {log_lines} lines)',
                        [f'Complete log: {result["log"]}', '', *clean] if clean else ['No log output.'])


def _positive(value):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('must be a positive finite number') from exc
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be a positive finite number')
    return number


def _parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', type=Path, help='Input recording (read without modification).')
    parser.add_argument('-p', '--parameters', '--params', type=Path,
                        default=ROOT / 'parameters/default_parameters_default.yaml', help='YAML/JSON parameters.')
    parser.add_argument('--pipeline', help='Override pipeline_name from the parameters.')
    parser.add_argument('--end-frame', '--end_frame', type=int, help='Override exclusive end_frame; <=0 uses the entire recording.')
    parser.add_argument('--mode', choices=('both', 'preview', 'process'), default='both')
    parser.add_argument('--backend', choices=('auto', 'numpy', 'cupy'), help='Override backend/force_numpy; unavailable CUDA falls back to NumPy.')
    parser.add_argument('--interval', type=_positive, default=.2, help='CPU/RAM sampling target in seconds (default: 0.2).')
    parser.add_argument('--gpu-interval', type=_positive, default=1., help='Minimum delay between NVIDIA observations (default: 1 s).')
    parser.add_argument('--gpu-timeout', type=_positive, default=3., help='Timeout per NVIDIA query (default: 3 s).')
    parser.add_argument('--timeout', type=_positive, help='Maximum worker wall time per mode, including startup; still writes a failure report.')
    parser.add_argument('--log-lines', type=int, default=200, help='Tail lines per mode included in PDF; full logs are always saved.')
    parser.add_argument('--report', type=Path, default=ROOT / 'temp/benchmark/report.pdf', help='PDF destination.')
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    for name in ('file', 'parameters'):
        path = getattr(args, name).expanduser().resolve()
        if not path.is_file():
            parser.error(f'{name} does not exist: {path}')
        setattr(args, name, path)
    if args.log_lines < 1:
        parser.error('--log-lines must be positive')
    try:
        import psutil
    except ImportError:
        parser.error("psutil is required; install with: pip install -e '.[benchmark]'")
    from holodoppler.config import load_config
    from holodoppler.pipelines import pipelines
    from yaml import YAMLError
    try:
        parameters = load_config(args.parameters)
        if not isinstance(parameters, dict):
            raise ValueError('parameters must be a mapping')
    except (OSError, ValueError, TypeError, YAMLError) as exc:
        parser.error(str(exc))
    if args.pipeline:
        parameters['pipeline_name'] = args.pipeline
    name = parameters.get('pipeline_name')
    modes = ('preview', 'process') if args.mode == 'both' else (args.mode,)
    if not isinstance(name, str) or name.startswith('preview_') or any(
            (f'preview_{name}' if mode == 'preview' else name) not in pipelines for mode in modes):
        parser.error(f'Unknown pipeline {name!r}; available: {", ".join(key for key in pipelines if not key.startswith("preview_"))}')
    if args.end_frame is not None:
        parameters['end_frame'] = args.end_frame
    report = args.report.expanduser().resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    directory = report.parent / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True)
    os.environ.setdefault('MPLCONFIGDIR', str(directory / 'matplotlib'))
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), file=str(args.file),
                    file_size_bytes=args.file.stat().st_size, parameters_file=str(args.parameters),
                    parameters=parameters, backend=args.backend, directory=str(directory), report=str(report),
                    system=platform.platform(), python=sys.version, logical_cpus=psutil.cpu_count(),
                    system_ram_mib=psutil.virtual_memory().total / MIB,
                    interval=args.interval, gpu_interval=args.gpu_interval)
    config_path = directory / 'run.json'
    _write_json(config_path, manifest)
    results = []
    for stage in modes:
        print(f'Benchmarking {stage}: {name} ({args.file.name})', flush=True)
        result = _run_stage(config_path, stage, directory, args, psutil)
        results.append(result)
        print(f'  {result["status"]}; API wall {_format(result["call_seconds"], " s")}', flush=True)
        if result['status'] == 'interrupted':
            break
    _save_samples(directory, results)
    _write_json(directory / 'summary.json', dict(manifest=manifest, results=[
        {key: value for key, value in result.items() if key not in ('cpu', 'gpu', 'events')} for result in results]))
    _report(report, manifest, results, args.log_lines)
    print(f'Report: {report}\nRaw metrics, logs, and pipeline outputs: {directory}', flush=True)
    return 0 if all(result['status'] == 'success' for result in results) else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '_worker':
        raise SystemExit(_worker(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
