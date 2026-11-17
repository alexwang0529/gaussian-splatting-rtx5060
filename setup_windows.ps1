param([string]$Python = '')
$ErrorActionPreference = 'Stop'
$taskProject = $PSScriptRoot
if (-not $Python) {
    $taskEnvs = (& conda env list --json | ConvertFrom-Json).envs
    $taskPrefix = $taskEnvs | Where-Object { (Split-Path $_ -Leaf) -eq 'gaussian-splatting' } | Select-Object -First 1
    if (-not $taskPrefix) { throw 'Create the gaussian-splatting environment from environment.windows-cu128.yml first.' }
    $Python = Join-Path $taskPrefix 'python.exe'
}
$Python = (Resolve-Path -LiteralPath $Python).Path
$taskPrefix = Split-Path $Python
$taskVsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$taskVs = & $taskVsWhere -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.14.38.17.8.x86.x64 -property installationPath | Select-Object -First 1
if (-not $taskVs) { throw 'Install Visual Studio 2022 with MSVC 14.38 x64/x86 and a Windows SDK.' }
Import-Module (Join-Path $taskVs 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $taskVs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'
$env:CUDA_HOME = Join-Path $env:ProgramFiles 'NVIDIA GPU Computing Toolkit\CUDA\v12.8'
if (-not (Test-Path -LiteralPath "$env:CUDA_HOME\bin\nvcc.exe")) { throw 'Install CUDA Toolkit 12.8 first.' }
$env:CUDA_PATH = $env:CUDA_HOME
$env:CONDA_PREFIX = $taskPrefix
$env:Path = "$taskPrefix;$taskPrefix\Library\bin;$taskPrefix\Scripts;$env:CUDA_HOME\bin;$env:Path"
$env:PYTHONUTF8 = '1'
$env:TORCH_CUDA_ARCH_LIST = '12.0'
$env:DISTUTILS_USE_SDK = '1'
$env:MAX_JOBS = '2'
$env:VSLANG = '1033'
Push-Location -LiteralPath $taskProject
try {
    & $Python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed.' }
    & $Python -m pip install -r requirements.windows.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    foreach ($taskModule in @('simple-knn','diff-gaussian-rasterization','fused-ssim')) {
        # Older ANSI build files cannot be read after enabling Python UTF-8 mode.
        $taskCache = Join-Path $taskProject "submodules\$taskModule\build\temp.win-amd64-cpython-310\Release\build.ninja"
        if (Test-Path -LiteralPath $taskCache) { Remove-Item -LiteralPath $taskCache }
        & $Python -m pip install --no-deps --no-build-isolation --no-cache-dir -v ".\submodules\$taskModule"
        if ($LASTEXITCODE -ne 0) { throw "Extension build failed: $taskModule" }
    }
    & $Python scripts\verify_gpu.py
    if ($LASTEXITCODE -ne 0) { throw 'GPU verification failed.' }
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed.' }
} finally { Pop-Location }
