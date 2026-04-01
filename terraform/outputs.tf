output "instance_ip" {
  description = "Public IP address of the VM"
  value       = google_compute_instance.ai_kb.network_interface[0].access_config[0].nat_ip
}

output "app_url" {
  description = "URL of the application"
  value       = "http://${google_compute_instance.ai_kb.network_interface[0].access_config[0].nat_ip}"
}
