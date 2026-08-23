[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9-]{2,58}$')]
    [string]$AppName,
    [string]$ResourceGroup = 'rg-invoice-review-student-uae',
    [string]$Location = 'uaenorth',
    [string]$SubscriptionId = 'ddb20c37-b7f8-4d97-9834-afa830563657'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$planName = "$AppName-plan"

az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { throw 'Could not select the approved Azure for Students subscription.' }

& (Join-Path $PSScriptRoot 'stage-appservice.ps1')

az group create --name $ResourceGroup --location $Location
if ($LASTEXITCODE -ne 0) { throw 'Resource group creation failed.' }

# F1 is intentional: never change this script to a paid SKU for the student demo.
az appservice plan create --name $planName --resource-group $ResourceGroup --location $Location --sku F1 --is-linux
if ($LASTEXITCODE -ne 0) { throw 'Azure did not accept the required F1 Free App Service plan.' }

az webapp create --name $AppName --resource-group $ResourceGroup --plan $planName --runtime 'PYTHON:3.12'
if ($LASTEXITCODE -ne 0) { throw 'Web app creation failed.' }

az webapp config set --name $AppName --resource-group $ResourceGroup --startup-file 'python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'
az webapp config appsettings set --name $AppName --resource-group $ResourceGroup --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true

Push-Location $backendRoot
try {
    Compress-Archive -Path @('app', 'static', 'pyproject.toml', 'uv.lock') -DestinationPath (Join-Path $env:TEMP 'invoice-review-appservice.zip') -Force
    az webapp deploy --name $AppName --resource-group $ResourceGroup --src-path (Join-Path $env:TEMP 'invoice-review-appservice.zip') --type zip --track-status false
    if ($LASTEXITCODE -ne 0) { throw 'Application deployment failed.' }
}
finally {
    Pop-Location
}

Write-Output "Deployed: https://$AppName.azurewebsites.net"
Write-Output 'Add the existing Azure AI environment settings in App Service before using document processing.'
