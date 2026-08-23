targetScope = 'subscription'

@description('The Azure region selected for this student demonstration.')
param location string = 'uaenorth'

@description('Resource group for the free-tier demonstration.')
param resourceGroupName string = 'rg-invoice-review-student-uae'

@description('Globally unique name for the App Service web app.')
param appName string

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module appService 'modules/app-service.bicep' = {
  name: 'invoice-review-app-service'
  scope: resourceGroup
  params: {
    appName: appName
    location: location
  }
}
