# KMS Keyring for OAuth credential encryption
resource "google_kms_key_ring" "oauth" {
  name     = "oauth-keyring"
  location = var.region
}

# KMS Key for encrypting OAuth credentials in Firestore
resource "google_kms_crypto_key" "oauth_credentials" {
  name            = "oauth-credentials-key"
  key_ring        = google_kms_key_ring.oauth.id
  rotation_period = "7776000s" # 90 days — auto-rotate quarterly

  lifecycle {
    prevent_destroy = true
  }
}

# Grant Cloud Run SA permission to encrypt/decrypt using this key
resource "google_kms_crypto_key_iam_member" "run_sa_kms" {
  crypto_key_id = google_kms_crypto_key.oauth_credentials.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.cloud_run.email}"
}