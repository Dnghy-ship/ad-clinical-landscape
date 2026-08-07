$ErrorActionPreference = "Continue"

Write-Host "=== Current directory ===" -ForegroundColor Cyan
Get-Location

Write-Host "`n=== Python ===" -ForegroundColor Cyan
python --version
where.exe python
python -c "import sys; print('executable =', sys.executable); print('version =', sys.version)"

Write-Host "`n=== Conda ===" -ForegroundColor Cyan
conda --version
conda info --envs

Write-Host "`n=== Core Python packages ===" -ForegroundColor Cyan
python -c "import requests,pandas,plotly,openpyxl,yaml; print('requests',requests.__version__); print('pandas',pandas.__version__); print('plotly',plotly.__version__); print('openpyxl',openpyxl.__version__); print('PyYAML',yaml.__version__)"

Write-Host "`n=== Streamlit ===" -ForegroundColor Cyan
python -c "import streamlit; print('streamlit',streamlit.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Streamlit missing. Install project: python -m pip install -e ." -ForegroundColor Yellow
}

Write-Host "`n=== ClinicalTrials.gov API ===" -ForegroundColor Cyan
try {
  $r = Invoke-RestMethod -Uri "https://clinicaltrials.gov/api/v2/version" -TimeoutSec 20
  $r | ConvertTo-Json -Depth 5
} catch {
  Write-Host "API connectivity failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Conda profile hint ===" -ForegroundColor Cyan
Write-Host 'If startup references Temp\_MEI...\Conda.psm1, run:'
Write-Host '  & "C:\Miniconda3\Scripts\conda.exe" init powershell'
Write-Host 'Then reopen PowerShell; if needed inspect: notepad $PROFILE'
