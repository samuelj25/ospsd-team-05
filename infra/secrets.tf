resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "calendar-client-service-gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "slack_bot_token" {
  secret_id = "calendar-client-service-slack-bot-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "slack_signing_secret" {
  secret_id = "calendar-client-service-slack-signing-secret"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gcp_credentials" {
  secret_id = "calendar-client-service-gcp-credentials"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gcp_token" {
  secret_id = "calendar-client-service-gcp-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_oauth_client_id" {
  secret_id = "calendar-client-service-oauth-client-id"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_oauth_client_secret" {
  secret_id = "calendar-client-service-oauth-client-secret"
  replication {
    auto {}
  }
}