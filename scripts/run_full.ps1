$ErrorActionPreference = "Stop"
python -m pip install -e .
python -m unittest discover -s tests -v
python -m adtrial doctor
python -m adtrial all
Write-Host "Finished. Open output\ad_competitive_landscape.html" -ForegroundColor Green
Write-Host "Interactive dashboard: adtrial dashboard" -ForegroundColor Green
