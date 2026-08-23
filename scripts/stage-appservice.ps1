[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'
$backendRoot = Join-Path $projectRoot 'backend'
$staticRoot = Join-Path $backendRoot 'static'

Push-Location $frontendRoot
try {
    pnpm build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' }
}
finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $staticRoot | Out-Null
Get-ChildItem -LiteralPath $staticRoot -Force | Remove-Item -Recurse -Force
Copy-Item -Path (Join-Path $frontendRoot 'dist\*') -Destination $staticRoot -Recurse -Force

Write-Output "Staged frontend assets in $staticRoot"
