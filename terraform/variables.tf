# ---------------------------------------------------------------------------
# Render platform credentials
# ---------------------------------------------------------------------------

variable "render_api_key" {
  description = "Render API key — generate from Render dashboard > Account Settings > API Keys"
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "Render owner/team ID — visible in the Render dashboard URL: dashboard.render.com/teams/<owner_id>"
  type        = string
}

variable "render_service_id" {
  description = "Render service ID — visible in the Render dashboard URL when viewing the service (e.g. srv-xxxxxxxx). Used for terraform import only."
  type        = string
}

# ---------------------------------------------------------------------------
# Google OAuth 2.0 credentials
# ---------------------------------------------------------------------------

variable "google_oauth_client_id" {
  description = "Google OAuth 2.0 Client ID from GCP Console > APIs & Services > Credentials"
  type        = string
  sensitive   = true
}

variable "google_oauth_client_secret" {
  description = "Google OAuth 2.0 Client Secret from GCP Console"
  type        = string
  sensitive   = true
}

variable "oauth_redirect_uri" {
  description = "OAuth 2.0 redirect URI registered in GCP Console"
  type        = string
  default     = "https://ospsd-team-05.onrender.com/auth/callback"
}

variable "google_calendar_id" {
  description = "Google Calendar ID to operate on (use primary for the default calendar)"
  type        = string
  default     = "primary"
}

# ---------------------------------------------------------------------------
# Session security
# ---------------------------------------------------------------------------

variable "session_secret" {
  description = "Secret key for signing session cookies — must be a long random string in production"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# GCP credentials for CI
# ---------------------------------------------------------------------------

variable "gcp_credentials_json_base64" {
  description = "Base64-encoded contents of credentials.json — used by CircleCI integration/e2e jobs"
  type        = string
  sensitive   = true
}

variable "gcp_token_json_base64" {
  description = "Base64-encoded contents of token.json — used by CircleCI integration/e2e jobs"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# HW3 — AI integration
# ---------------------------------------------------------------------------

variable "gemini_api_key" {
  description = "Gemini API key for AI integration — get from aistudio.google.com > Get API Key"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# HW3 - Chat integration
# ---------------------------------------------------------------------------

 variable "slack_bot_token" {
   description = "Slack bot token for chat integration"
   type        = string
   sensitive   = true
}