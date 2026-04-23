output "service_url" {
  description = "The live URL of the deployed calendar service"
  value       = "https://ospsd-team-05.onrender.com"
}

output "health_check_url" {
  description = "Health check endpoint — should return HTTP 200"
  value       = "https://ospsd-team-05.onrender.com/health"
}

output "openapi_url" {
  description = "OpenAPI spec endpoint — used to regenerate the API client"
  value       = "https://ospsd-team-05.onrender.com/openapi.json"
}

output "metrics_url" {
  description = "Prometheus metrics endpoint — scraped by Grafana for telemetry dashboards"
  value       = "https://ospsd-team-05.onrender.com/metrics"
}