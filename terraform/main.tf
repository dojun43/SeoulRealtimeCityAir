# 고정 ip
resource "google_compute_address" "static_ip" {
  name   = "seoulrealtimecityair-static-ip"
  project = var.project
  region  = var.region
}

# port 허용 
resource "google_compute_firewall" "allow-streamlit" {
  name    = "allow-streamlit"
  project = var.project
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8501"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-streamlit"]
}

resource "google_compute_firewall" "allow-postgres" {
  name    = "allow-postgres"
  project = var.project
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5431","5432"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-postgres"]
}

resource "google_compute_firewall" "allow-airflow-webserver" {
  name    = "allow-airflow-webserver"
  project = var.project
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-airflow-webserver"]
}

resource "google_compute_firewall" "allow-ssh" {
  name    = "allow-ssh"
  project = var.project
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-ssh"]
}

# gce
resource "google_compute_instance" "default" {
  name         = "seoulrealtimecityair-gce"
  machine_type = "n2-standard-4"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.static_ip.address
    }
  }

  metadata_startup_script = file("startup_script.sh")

  tags = ["allow-ssh", "allow-airflow-webserver", "allow-streamlit", "allow-postgres"]
}