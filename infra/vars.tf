variable "service_account_id" {
  description = "The ID of the service account to create."
  type        = string
}

variable "service_account_display_name" {
  description = "The display name of the service account."
  type        = string
}

variable "input_bucket_name" {
  description = "The name of the input data storage bucket."
  type        = string
}

variable "result_bucket_name" {
  description = "The name of the result data storage bucket."
  type        = string
}
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region."
  type        = string
}
