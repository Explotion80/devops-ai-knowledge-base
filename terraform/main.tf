terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Firewall — allow HTTP (port 80)
resource "google_compute_firewall" "allow_http" {
  name    = "allow-http-ai-kb"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

# Firewall — allow SSH (port 22)
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh-ai-kb"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh-server"]
}

# VM instance
resource "google_compute_instance" "ai_kb" {
  name         = "ai-kb-server"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["http-server", "ssh-server"]

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh", {
    openai_api_key = var.openai_api_key
  })
}
