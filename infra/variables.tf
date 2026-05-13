variable "project_id" { type = string }
variable "region"     { type = string }
variable "service_name" { type = string }
variable "image_url"  { type = string }
variable "enable_service" {
  type    = bool
  default = true
}
variable "gemini_model" {
  type        = string
  default     = "gemini-2.5-flash"
  description = "The Gemini AI model to use for AI tool"
}