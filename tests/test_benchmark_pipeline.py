"""Benchmark reports must survive failed calls and preserve original recordings/outputs."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import h5py
import numpy as np
import pytest
import yaml

pytest.importorskip('psutil')
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/benchmark_pipeline.py'
spec = importlib.util.spec_from_file_location('benchmark_pipeline', SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_gpu_parsing_distinguishes_zero_missing_and_multiple_processes():
    devices = benchmark._gpu_devices('0, GPU-one, Test GPU, 250, 8192, 30, 12\n'
                                     '1, GPU-two, Other GPU, N/A, 4096, [Not Supported], 0\n')
    assert devices[0]['vram_used_mib'] == 250
    assert devices[1]['vram_used_mib'] is None
    assert devices[1]['gpu_percent'] is None
    memory = benchmark._process_vram('GPU-one, 10, 100\nGPU-one, 11, 25\n'
                                     'GPU-one, 99, 900\nGPU-two, 10, N/A\n', {10, 11})
    assert memory == {'GPU-one': 125, 'GPU-two': None}


def test_nvidia_polling_never_waits_for_a_running_query(monkeypatch):
    monkeypatch.setattr(benchmark.shutil, 'which', lambda name: '/fake/nvidia-smi')
    commands = []
    class Query:
        def __init__(self, command, **kwargs):
            self.command = command
            self.returncode = None
            self.communicated = False
            commands.append(self)
        def poll(self):
            return self.returncode
        def communicate(self):
            assert self.returncode == 0
            self.communicated = True
            if '--query-gpu=' in self.command[1]:
                return '0, GPU-one, Test GPU, 200, 8192, 50, 20\n', ''
            return 'GPU-one, 10, 150\nGPU-one, 11, 20\n', ''
    monkeypatch.setattr(benchmark.subprocess, 'Popen', Query)
    sampler = benchmark.NvidiaSampler(interval=1, timeout=3)
    assert sampler.tick({10, 11}) is None
    for _ in range(3):
        assert sampler.tick({10, 11}) is None
    assert not commands[0].communicated
    commands[0].returncode = 0
    assert sampler.tick({10, 11}) is None
    assert len(commands) == 2
    commands[1].returncode = 0
    sample = sampler.tick({10, 11})
    assert sample['devices'][0]['process_vram_mib'] == 170
    sampler.close()


def test_nvidia_driver_failure_disables_queries_without_faking_zeroes(monkeypatch):
    monkeypatch.setattr(benchmark.shutil, 'which', lambda name: '/fake/nvidia-smi')
    query = SimpleNamespace(returncode=9, poll=lambda: 9,
                            communicate=lambda: ('', 'Driver unavailable'))
    launch = []
    def popen(*args, **kwargs):
        launch.append(args)
        return query
    monkeypatch.setattr(benchmark.subprocess, 'Popen', popen)
    sampler = benchmark.NvidiaSampler(interval=1, timeout=3)
    sampler.tick({10})
    assert sampler.tick({10}) is None
    assert sampler.disabled
    assert 'Driver unavailable' in sampler.warnings[0]
    assert sampler.tick({10}) is None
    assert len(launch) == 1


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf'])
def test_invalid_sampling_intervals_are_rejected(value):
    with pytest.raises(SystemExit):
        benchmark._parser().parse_args(['input.holo', '--interval', value])


@pytest.fixture
def recording(tmp_path):
    from scripts.make_synthetic_test_data import create_holo
    path = tmp_path / 'recording.holo'
    create_holo(path, np.random.default_rng(10).integers(0, 4096, (32, 24, 32), dtype=np.uint16), bit_depth=16)
    params = yaml.safe_load((ROOT / 'parameters/default_parameters_default.yaml').read_text())
    normal_output = tmp_path / 'normal-output'
    normal_output.mkdir()
    (normal_output / 'keep.txt').write_text('Do not overwrite')
    params.update(backend="numpy", custom_path=str(normal_output),
                  batch_size=8, batch_stride=8, first_frame=0, end_frame=-1,
                  sampling_freq=1000, low_freq=100, high_freq=400,
                  pixel_pitch=[1e-6, 1e-6], z=.1, svd_threshold=2,
                  numpy_num_workers=1, num_saving_workers=0,
                  image_registration=False, shack_hartmann_autofocus=False,
                  frequency_bands=[], color_Doppler_image=False, directional_Doppler_image=False,
                  save_spectograms=False, save_averaged_spectrogram=False,
                  lsci_enable_temporal=False, lsci_enable_spatiotemporal=False)
    parameters = tmp_path / 'parameters.yaml'
    parameters.write_text(yaml.safe_dump(params))
    return path, parameters, normal_output


def invoke(recording, report, *options):
    path, parameters, _ = recording
    return subprocess.run([sys.executable, str(SCRIPT), str(path), '-p', str(parameters),
                           '--report', str(report), '--interval', '.05', '--log-lines', '20',
                           *options], cwd=ROOT, capture_output=True, text=True, timeout=90)


@pytest.mark.parametrize('pipeline', ['default', 'lsci'])
def test_real_preview_process_report_and_end_frame_override(recording, tmp_path, pipeline):
    path, _, normal_output = recording
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    report = tmp_path / 'benchmark/report.pdf'
    result = invoke(recording, report, '--pipeline', pipeline, '--end_frame=16', '--timeout', '30')
    assert result.returncode == 0, result.stdout + result.stderr
    pdf = report.read_bytes()
    assert pdf.startswith(b'%PDF-')
    assert pdf.count(b'/Type /Page') >= 6
    summary_file = next(report.parent.glob('runs/*/summary.json'))
    summary = json.loads(summary_file.read_text())
    directory = summary_file.parent
    stages = summary['results']
    assert [stage['stage'] for stage in stages] == ['preview', 'process']
    assert all(stage['status'] == 'success' and stage['call_seconds'] > 0 for stage in stages)
    assert stages[0]['pid'] != stages[1]['pid']
    assert summary['manifest']['parameters']['end_frame'] == 16
    with (directory / 'cpu.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    assert {row['stage'] for row in rows} == {'preview', 'process'}
    assert all(float(row['rss_mib']) >= 0 for row in rows)
    assert (directory / 'gpu.csv').is_file()
    for stage in ('preview', 'process'):
        assert (directory / f'{stage}.log').stat().st_size > 0
        assert (directory / f'{stage}.parameters.json').is_file()
    with h5py.File(directory / 'process-output/h5/process-output_output.h5') as handle:
        key = 'moment0' if pipeline == 'default' else 'spatial_flow_index'
        assert handle[key].shape[0] == 2  # 16 source frames / 8 frames per batch.
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert (normal_output / 'keep.txt').read_text() == 'Do not overwrite'
    assert sorted(item.name for item in normal_output.iterdir()) == ['keep.txt']
    assert not (path.parent / path.stem / f'{path.stem}_HD').exists()


def test_failed_pipeline_still_produces_report_with_traceback(recording, tmp_path):
    parameters = recording[1]
    params = yaml.safe_load(parameters.read_text())
    params['low_freq'] = 'invalid'
    parameters.write_text(yaml.safe_dump(params))
    report = tmp_path / 'failed/report.pdf'
    result = invoke(recording, report, '--mode', 'preview')
    assert result.returncode == 1, result.stdout + result.stderr
    assert report.read_bytes().startswith(b'%PDF-')
    summary_file = next(report.parent.glob('runs/*/summary.json'))
    summary = json.loads(summary_file.read_text())
    assert summary['results'][0]['status'] == 'failed'
    assert 'low_freq' in summary['results'][0]['error']
    log = (summary_file.parent / 'preview.log').read_text()
    assert 'Traceback' in log and 'low_freq' in log


def test_worker_timeout_still_produces_report(recording, tmp_path):
    report = tmp_path / 'timeout/report.pdf'
    result = invoke(recording, report, '--mode', 'process', '--timeout', '.001')
    assert result.returncode == 1, result.stdout + result.stderr
    assert report.read_bytes().startswith(b'%PDF-')
    summary = json.loads(next(report.parent.glob('runs/*/summary.json')).read_text())
    assert summary['results'][0]['status'] == 'timeout'
