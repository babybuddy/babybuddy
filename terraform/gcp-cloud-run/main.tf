provider "google" {
  region = var.region
}

resource "google_project" "baby_buddy" {
  name                = var.project_name
  project_id          = var.project_id
  billing_account     = var.billing_account
  auto_create_network = false
}

locals {
  services = toset(["run.googleapis.com",
    "sqladmin.googleapis.com",
    "sql-component.googleapis.com",
    "secretmanager.googleapis.com"
  ])
}

resource "google_project_service" "project_services" {
  for_each                   = local.services
  project                    = google_project.baby_buddy.project_id
  service                    = each.value
  disable_on_destroy         = true
  disable_dependent_services = true
}

resource "random_password" "root_password" {
  min_lower   = 1
  min_numeric = 1
  min_upper   = 1
  length      = 19
  special     = true
  min_special = 1
  lifecycle {
    ignore_changes = [
      min_lower, min_upper, min_numeric, special, min_special, length
    ]
  }
}

resource "random_password" "django_secret_key" {
  min_lower   = 1
  min_numeric = 1
  min_upper   = 1
  length      = 20
  special     = true
  min_special = 1
  lifecycle {
    ignore_changes = [
      min_lower, min_upper, min_numeric, special, min_special, length
    ]
  }
}

resource "google_sql_database_instance" "baby_buddy" {
  name             = "babybuddy"
  database_version = "POSTGRES_15"
  root_password    = random_password.root_password.result
  settings {
    tier                        = "db-f1-micro"
    disk_autoresize             = false
    deletion_protection_enabled = false
    insights_config {
      query_insights_enabled = false
    }
    maintenance_window {
      day  = 1
      hour = 0
    }
  }

  deletion_protection = "true"
}

resource "google_secret_manager_secret" "postgres_password" {
  secret_id = "postgres-password"
  project   = google_project.baby_buddy.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "postgres_password" {
  secret      = google_secret_manager_secret.postgres_password.name
  secret_data = google_sql_database_instance.baby_buddy.root_password
}

resource "google_secret_manager_secret_iam_member" "postgres_password" {
  secret_id  = google_secret_manager_secret.postgres_password.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_project.baby_buddy.number}-compute@developer.gserviceaccount.com"
  depends_on = [google_secret_manager_secret.postgres_password]
}

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key"
  project   = google_project.baby_buddy.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.name
  secret_data = random_password.django_secret_key.result
}

resource "google_secret_manager_secret_iam_member" "django_secret_key" {
  secret_id  = google_secret_manager_secret.django_secret_key.name
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_project.baby_buddy.number}-compute@developer.gserviceaccount.com"
  depends_on = [google_secret_manager_secret.django_secret_key]
}

resource "google_cloud_run_v2_service" "baby_buddy" {
  name     = "babybuddy"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  project  = google_project.baby_buddy.project_id

  template {
    scaling {
      max_instance_count = 2
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.baby_buddy.connection_name]
      }
    }

    containers {
      name  = "babybuddy-1"
      image = "docker.io/linuxserver/babybuddy:latest"

      env {
        name  = "DB_HOST"
        value = "/cloudsql/${google_project.baby_buddy.project_id}:${var.region}:${google_sql_database_instance.baby_buddy.name}"
      }
      env {
        name  = "DB_USER"
        value = "postgres"
      }
      env {
        name  = "DB_NAME"
        value = "postgres"
      }
      env {
        name  = "DB_ENGINE"
        value = "django.db.backends.postgresql"
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.secret_id
            version = google_secret_manager_secret_version.postgres_password.version
          }
        }
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.django_secret_key.secret_id
            version = google_secret_manager_secret_version.django_secret_key.version
          }
        }
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  annotations = {
    "foo" = "bar"
  }
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  depends_on = [google_secret_manager_secret_version.postgres_password, google_secret_manager_secret_version.django_secret_key]
}
