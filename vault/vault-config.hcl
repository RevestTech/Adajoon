ui = true

# Storage backend — file storage for single-node Railway deployment.
# Data persists in /vault/data (Railway volume mount).
storage "file" {
  path = "/vault/data"
}

# Listener — HTTP for Railway internal networking.
# Railway handles TLS termination at its proxy layer.
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

# Disable mlock for container environments
disable_mlock = true

# Telemetry
telemetry {
  disable_hostname = true
}
