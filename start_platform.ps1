$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$platformPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $platformPython)) {
    throw 'Missing .venv. Run: py -3.12 -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
}
& $platformPython -m streamlit run app.py --server.port=8501
