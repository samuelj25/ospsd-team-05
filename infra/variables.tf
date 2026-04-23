variable "project_id" { type = string }
variable "region"     { type = string }
variable "service_name" { type = string }
variable "image_url"  { type = string }
variable "enable_service" {
  type    = bool
  default = true
}