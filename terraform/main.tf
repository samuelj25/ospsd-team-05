terraform {
  required_version = ">= 1.5.0"

  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.3"
    }
  }
}

provider "render" {
  api_key  = var.render_api_key
  owner_id = var.render_owner_id
}

resource "render_web_service" "calendar_service" {
  name   = "ospsd-team-05"
  region = "virginia"
  plan   = "free"w

  runtime_source = {
    docker = {
      repo_url        = "https://github.com/samuelj25/ospsd-team-05"
      branch          = "main"
      dockerfile_path = "./Dockerfile"
      context         = "."
    }
  }

  health_check_path = "/health"

  env_vars = {

    # Google OAuth 2.0 credentials
    GOOGLE_OAUTH_CLIENT_ID = {
      value = var.google_oauth_client_id
    }

    GOOGLE_OAUTH_CLIENT_SECRET = {
      value = var.google_oauth_client_secret
    }

    OAUTH_REDIRECT_URI = {
      value = var.oauth_redirect_uri
    }

    GOOGLE_CALENDAR_ID = {
      value = var.google_calendar_id
    }

    # Session security
    GOOGLE_CALENDAR_SESSION_SECRET = {
      value = var.session_secret
    }

    GOOGLE_CALENDAR_SESSION_COOKIE_SECURE = {
      value = "true"
    }

    # GCP credentials for CI (base64-encoded JSON)
    GCP_CREDENTIALS_JSON_BASE64 = {
      value = var.gcp_credentials_json_base64
    }

    GCP_TOKEN_JSON_BASE64 = {
      value = var.gcp_token_json_base64
    }

    # HW3 — AI integration (Google Gemini)
    GEMINI_API_KEY = {
      value = var.gemini_api_key
    }

    # HW3 — Chat vertical integration
    SLACK_BOT_TOKEN = {
      value = var.slack_bot_token
    }
  }
}