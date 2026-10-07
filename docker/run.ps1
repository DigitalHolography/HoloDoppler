<#
.SYNOPSIS
Process every recording in input/ with settings from config/parameters.yaml.
.EXAMPLE
./run.ps1 -Gpu
.EXAMPLE
./run.ps1 -Build
#>
[CmdletBinding()]
param(
    [switch]$Gpu,
    [switch]$Build,
    [switch]$Preview,
    [switch]$Recursive
)

$ErrorActionPreference = 'Stop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Install and start Docker Desktop with the WSL 2 engine first.'
}
foreach ($folder in @('input', 'config', 'output')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot $folder) | Out-Null
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'config/parameters.yaml') -PathType Leaf)) {
    throw 'Missing config/parameters.yaml. Restore the default settings from the starter download.'
}
$dockerOs = & docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) {
    throw 'Docker is unavailable. Start Docker Desktop and wait until its Linux engine is running.'
}
if ($dockerOs -ne 'linux') { throw 'Switch Docker Desktop to Linux containers and try again.' }

$service = if ($Gpu) { 'gpu' } else { 'cpu' }
$composeArgs = @('compose', '-f', (Join-Path $PSScriptRoot 'compose.yaml'))
if ($Build) {
    $buildFile = Join-Path $PSScriptRoot 'compose.build.yaml'
    if (-not (Test-Path -LiteralPath $buildFile)) {
        throw '-Build needs the source repository. Starter users can run without -Build.'
    }
    $composeArgs += @('-f', $buildFile)
    & docker @composeArgs build $service
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$mode = if ($Preview) { 'preview' } else { 'process' }
$runArgs = @('run', '--rm', '--no-deps', $service, $mode, '--folder', '/data',
    '/config/parameters.yaml', '--output-dir', '/output')
if ($Gpu) { $runArgs += '--require-gpu' }
if ($Recursive) { $runArgs += '--recursive' }
& docker @composeArgs @runArgs
exit $LASTEXITCODE
