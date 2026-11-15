const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL
const isSameOriginApp = window.location.port === '8000'
const apiBaseUrl = isSameOriginApp
  ? window.location.origin
  : configuredApiBaseUrl || 'http://localhost:8000'

export const env = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ''),
}
