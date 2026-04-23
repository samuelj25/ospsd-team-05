# Terraform — Infrastructure as Code

This directory manages the deployed infrastructure for `ospsd-team-05` using
[Terraform](https://www.terraform.io/) and the
[Render Terraform Provider](https://registry.terraform.io/providers/render-oss/render/latest).

## Prerequisites

- Terraform installed: `brew install terraform`
- Render API key from the account owner (Render dashboard > Account Settings > API Keys)
- Render service ID and owner ID from the Render dashboard

## Files

| File | Purpose |
|---|---|
| `main.tf` | Defines the Render web service, runtime, and all environment variables |
| `variables.tf` | Declares all input variables with types and descriptions |
| `outputs.tf` | Prints useful URLs after a successful apply |
| `terraform.tfvars.example` | Safe template showing what `terraform.tfvars` should look like |
| `.gitignore` | Ensures secrets and state files are never committed |

## First-Time Setup

```bash
# 1. Copy the example vars file and fill in real values
cp terraform.tfvars.example terraform.tfvars

# 2. Download the Render provider
terraform init

# 3. Import the existing Render service into Terraform state
#    (only needed once — the service was created manually in HW2)
terraform import render_web_service.calendar_service <render_service_id>

# 4. Preview what Terraform would change
terraform plan

# 5. Apply the configuration
terraform apply
```

## Adding Slack Integration Credentials

Now that Slack has been confirmed as the chat vertical integration:
1. Uncomment `slack_bot_token` in `variables.tf`
2. Uncomment the `SLACK_BOT_TOKEN` block in `main.tf`
3. Add the real Slack bot token to `terraform.tfvars`
4. Run `terraform apply`

To get a Slack bot token:
1. Go to `api.slack.com/apps`
2. Create a new app → From scratch
3. Add OAuth scopes: `chat:write`, `channels:read`, `channels:history`
4. Install to workspace
5. Copy the Bot User OAuth Token (starts with `xoxb-`)

## Getting Your Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API Key** → **Create API key**
4. Copy the key (starts with `AIza-`) into `terraform.tfvars` as `gemini_api_key`

Note: You can use the same GCP project already set up for Google Calendar.