# 📦 Portainer Service Inventory (Auto-Updated)

Automatically generate a live inventory of all containers, services, and exposed ports from a Portainer instance using the Portainer REST API.

Designed for home labs and self-hosted environments.

---

## 🧭 Overview

This project:

* Authenticates to Portainer API
* Retrieves Docker environment (endpoint)
* Lists all containers
* Extracts services and published ports
* Saves results to JSON
* Runs automatically on Synology Task Scheduler

Output is continuously updated and can be used for:

* service documentation
* dashboards
* monitoring
* reverse proxy reference
* infrastructure inventory

---

## 🧱 Requirements

* Portainer running and accessible
* Docker environment managed by Portainer
* Synology NAS (or any Linux host)
* curl
* jq

Install jq if needed:

```bash
sudo apt install jq
```

(Synology users can install via Package Center or Entware.)

---

## 🌐 Environment

Example setup:

```
Portainer URL: http://192.168.2.244:9000
```

---

## 🔐 Step 1 — Authenticate to Portainer API

Request a JWT token.

```bash
curl -X POST http://192.168.2.244:9000/api/auth \
  -H "Content-Type: application/json" \
  -d '{
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD"
  }'
```

Response:

```json
{
  "jwt": "TOKEN"
}
```

Copy the token.

---

## 🔎 Step 2 — Get Environment ID

Most installations only have one endpoint.

```bash
curl http://192.168.2.244:9000/api/endpoints \
  -H "Authorization: Bearer TOKEN"
```

Example response:

```json
[
  {
    "Id": 1,
    "Name": "local"
  }
]
```

Environment ID = `1`

---

## 📦 Step 3 — List Containers

```bash
curl http://192.168.2.244:9000/api/endpoints/1/docker/containers/json?all=true \
  -H "Authorization: Bearer TOKEN"
```

This returns full container metadata.

---

## 📋 Step 4 — Extract Service + Port Table

```bash
curl -s http://192.168.2.244:9000/api/endpoints/1/docker/containers/json?all=true \
  -H "Authorization: Bearer TOKEN" \
| jq -r '
  .[] |
  .Names[0] as $name |
  .Ports[]? |
  "\($name | ltrimstr("/")) | \(.IP // "0.0.0.0"):\(.PublicPort // "-") -> \(.PrivatePort)"
'
```

Example output:

```
portainer | 0.0.0.0:9000 -> 9000
nginx | 0.0.0.0:80 -> 80
nextcloud | 0.0.0.0:8443 -> 443
```

---

## 🤖 Step 5 — Automated Inventory Script

Create script:

```
/volume1/scripts/portainer_inventory.sh
```

```bash
#!/bin/bash

PORTAINER="http://192.168.2.244:9000"
USER="YOUR_USERNAME"
PASS="YOUR_PASSWORD"
OUTPUT="/volume1/web/containers.json"

TOKEN=$(curl -s -X POST "$PORTAINER/api/auth" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  | jq -r .jwt)

ENDPOINT=$(curl -s "$PORTAINER/api/endpoints" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[0].Id')

curl -s "$PORTAINER/api/endpoints/$ENDPOINT/docker/containers/json?all=true" \
  -H "Authorization: Bearer $TOKEN" \
  > "$OUTPUT"
```

Make executable:

```bash
chmod +x /volume1/scripts/portainer_inventory.sh
```

---

## ⏱ Step 6 — Schedule Automatic Updates (Synology)

DSM → Control Panel → Task Scheduler → Create → Scheduled Task → User Script

Command:

```bash
/volume1/scripts/portainer_inventory.sh
```

Recommended schedule:

```
Every 5 minutes
```

---

## 📁 Output

Example file:

```
/volume1/web/containers.json
```

Contains full container inventory from Portainer.

Can be consumed by:

* dashboards
* monitoring tools
* documentation generators
* Grafana
* web UI
* service catalogs

---

## ⭐ Optional Enhancements

### Add public URL labels to containers

```yaml
labels:
  service.url=https://app.home
  service.group=media
```

Then extract via API to build full service catalog.

---

### Generate HTML dashboard

Pipeline:

```
Portainer API → JSON → template → static webpage
```

---

### Group by stack

Use:

```
/api/stacks
```

---

### Multi-environment inventory

Loop through:

```
/api/endpoints
```

---

## 🧪 Example Use Cases

* home lab documentation
* infrastructure inventory
* change tracking
* network port audit
* reverse proxy mapping
* CMDB sync

---

## 📜 License

MIT — free to use and modify.
