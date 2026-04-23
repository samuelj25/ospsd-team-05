output "service_url" {
  description = "The public HTTPS URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.calendar_service[0].uri
}

output "service_name" {
  description = "The deployed Cloud Run service name."
  value       = google_cloud_run_v2_service.calendar_service[0].name
}

output "region" {
  description = "The GCP region the service is deployed to."
  value       = var.region
}
