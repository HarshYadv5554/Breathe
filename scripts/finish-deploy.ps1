# Run after: gh auth login (device flow at https://github.com/login/device)
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Set-Location "$PSScriptRoot\.."

Write-Host "==> Checking GitHub auth..."
gh auth status

Write-Host "==> Creating GitHub repo and pushing (skip if repo exists)..."
gh repo create Breathe-ESG --public --source=. --remote=origin --push 2>$null
if ($LASTEXITCODE -ne 0) {
  git remote set-url origin https://github.com/HarshYadv5554/Breathe-ESG.git
  git push -u origin main
}

Write-Host "==> Done. Next: Render Dashboard -> New Blueprint -> connect Breathe-ESG repo"
Write-Host "    Or open: https://dashboard.render.com/blueprints"
Write-Host "    Postgres 'breathe-db' is already created in your workspace."
