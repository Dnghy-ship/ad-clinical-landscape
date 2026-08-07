param(
  [Parameter(Mandatory=$true)]
  [string]$RepoUrl
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
  git init
}

git add .
git status

Write-Host ""
Write-Host "Review the staged files above." -ForegroundColor Yellow
Write-Host "If they look correct, run:" -ForegroundColor Cyan
Write-Host '  git commit -m "Initial release: AD clinical landscape v0.2"'
Write-Host '  git branch -M main'
Write-Host "  git remote add origin $RepoUrl"
Write-Host '  git push -u origin main'
