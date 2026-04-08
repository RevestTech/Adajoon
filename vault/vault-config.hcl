ui = true

# Storage backend — uses Raft (integrated storage) for single-node Railway deploy.
# Data persists in /vault/data (mount a Railway volume here).
storage "raft" {
  path    = "/vault/data"
  node_id = "vault-railway-1"
}

# Listener — HTTP for Railway internal networking.
# Railway handles TLS termination at its proxy layer.
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

# API address — set via env var in entrypoint
# api_addr is injected at runtime

# Disable mlock for container environments (Railway doesn't support it)
disable_mlock = true

# Telemetry
telemetry {
  disable_hostname = true
}
