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

## Adding HW3 Chat Integration Credentials

Once the chat team integration is confirmed:
1. Uncomment the relevant variable in `variables.tf`
2. Uncomment the relevant `env_vars` block in `main.tf`
3. Add the real value to `terraform.tfvars`
4. Run `terraform apply`

## Getting Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Navigate to API Keys
4. Create a new key and copy it into `terraform.tfvars` as `anthropic_api_key`