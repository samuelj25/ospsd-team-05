# Dedicated Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "calendar-client-run-sa"
  display_name = "Calendar Client Cloud Run SA"
}

# Grant SA access to each secret
resource "google_secret_manager_secret_iam_member" "run_sa_gemini" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_slack_token" {
  secret_id = google_secret_manager_secret.slack_bot_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_slack_signing" {
  secret_id = google_secret_manager_secret.slack_signing_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_gcp_creds" {
  secret_id = google_secret_manager_secret.gcp_credentials.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_gcp_token" {
  secret_id = google_secret_manager_secret.gcp_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_oauth_client_id" {
  secret_id = google_secret_manager_secret.google_oauth_client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_oauth_client_secret" {
  secret_id = google_secret_manager_secret.google_oauth_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "run_sa_cloud_trace" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "run_sa_cloud_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run service — gated by enable_service for 2-step bootstrap
resource "google_cloud_run_v2_service" "calendar_service" {
  count    = var.enable_service ? 1 : 0
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    containers {
      image = var.image_url

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SLACK_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.slack_bot_token.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SLACK_SIGNING_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.slack_signing_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GCP_CREDENTIALS_JSON_BASE64"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gcp_credentials.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GCP_TOKEN_JSON_BASE64"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gcp_token.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GOOGLE_OAUTH_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GOOGLE_OAUTH_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "OAUTH_REDIRECT_URI"
        value = "https://calendar-client-service-iozhebgpyq-uc.a.run.app/auth/callback"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8000
      }
    }

    timeout = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_secret_manager_secret_iam_member.run_sa_gemini,
    google_secret_manager_secret_iam_member.run_sa_slack_token,
    google_secret_manager_secret_iam_member.run_sa_slack_signing,
    google_secret_manager_secret_iam_member.run_sa_gcp_creds,
    google_secret_manager_secret_iam_member.run_sa_gcp_token,
    google_secret_manager_secret_iam_member.run_sa_oauth_client_id,
    google_secret_manager_secret_iam_member.run_sa_oauth_client_secret,
    google_project_iam_member.run_sa_cloud_trace,
    google_project_iam_member.run_sa_cloud_monitoring,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.enable_service ? 1 : 0
  name     = google_cloud_run_v2_service.calendar_service[0].name
  location = google_cloud_run_v2_service.calendar_service[0].location
  role     = "roles/run.invoker"
  member   = "allUsers"
}