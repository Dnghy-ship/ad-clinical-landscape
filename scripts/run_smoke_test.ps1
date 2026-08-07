$ErrorActionPreference = "Stop"
python -m pip install -e .
python -m unittest discover -s tests -v
python -m adtrial doctor
python -m adtrial collect --max-studies 100
python -m adtrial report
Write-Host "Smoke test completed." -ForegroundColor Green
