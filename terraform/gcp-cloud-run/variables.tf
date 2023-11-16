variable "project_name" {
  description = "project name"
  type        = string
}

variable "project_id" {
  description = "project id, remember the project id has to be unique"
  type        = string
}

variable "billing_account" {
  description = "value of the billing account id"
  type        = string

}
variable "region" {
  description = "which region to deploy to"
  type        = string
  default     = "europe-north1"
}
