import requests
import json
import os
from datetime import datetime

CONFIG_FILE = "config.txt"
OUTPUT_DIR = "output"


# --------------------------------------------------
# CONFIG LOADER
# --------------------------------------------------
def load_config(path):
    config = {}
    with open(path) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k.strip()] = v.strip()

    config["VERIFY_SSL"] = config.get("VERIFY_SSL", "true").lower() == "true"
    return config


# --------------------------------------------------
# API CLIENT
# --------------------------------------------------
class PortainerClient:
    def __init__(self, base_url, username, password, verify_ssl=True):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = None

    def authenticate(self):
        url = f"{self.base_url}/api/auth"
        r = requests.post(
            url,
            json={"username": self.username, "password": self.password},
            verify=self.verify_ssl,
        )
        r.raise_for_status()
        self.token = r.json()["jwt"]

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_endpoints(self):
        url = f"{self.base_url}/api/endpoints"
        r = requests.get(url, headers=self.headers(), verify=self.verify_ssl)
        r.raise_for_status()
        return r.json()

    def get_containers(self, endpoint_id):
        url = f"{self.base_url}/api/endpoints/{endpoint_id}/docker/containers/json?all=true"
        r = requests.get(url, headers=self.headers(), verify=self.verify_ssl)
        r.raise_for_status()
        return r.json()


# --------------------------------------------------
# DATA EXTRACTION
# --------------------------------------------------
def build_service_record(container, public_host):
    name = container["Names"][0].lstrip("/")
    image = container.get("Image")
    state = container.get("State")

    ports = []
    urls = []

    for p in container.get("Ports", []):
        private = p.get("PrivatePort")
        public = p.get("PublicPort")
        ip = p.get("IP", "0.0.0.0")

        ports.append({
            "ip": ip,
            "public": public,
            "private": private,
            "type": p.get("Type")
        })

        if public:
            urls.append(f"http://{public_host}:{public}")

    networks = list(container.get("NetworkSettings", {}).get("Networks", {}).keys())

    return {
        "name": name,
        "image": image,
        "state": state,
        "ports": ports,
        "urls": urls,
        "networks": networks
    }


# --------------------------------------------------
# OUTPUT
# --------------------------------------------------
def save_json(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "containers.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("Saved:", path)


def save_table(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "containers_table.txt")

    with open(path, "w") as f:
        f.write(f"Generated: {datetime.now()}\n")
        f.write("=" * 70 + "\n")

        for ep in data:
            f.write(f"\nENDPOINT: {ep['endpoint_name']} (ID {ep['endpoint_id']})\n")
            f.write("-" * 70 + "\n")

            for c in ep["containers"]:
                f.write(f"Service : {c['name']}\n")
                f.write(f"Image   : {c['image']}\n")
                f.write(f"State   : {c['state']}\n")

                if c["urls"]:
                    for u in c["urls"]:
                        f.write(f"URL     : {u}\n")

                for p in c["ports"]:
                    f.write(
                        f"Port    : {p['ip']}:{p['public']} -> {p['private']} ({p['type']})\n"
                    )

                if c["networks"]:
                    f.write(f"Networks: {', '.join(c['networks'])}\n")

                f.write("\n")

    print("Saved:", path)


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    config = load_config(CONFIG_FILE)

    client = PortainerClient(
        config["PORTAINER_URL"],
        config["USERNAME"],
        config["PASSWORD"],
        config["VERIFY_SSL"],
    )

    print("Authenticating...")
    client.authenticate()

    print("Discovering endpoints...")
    endpoints = client.get_endpoints()

    inventory = []

    for ep in endpoints:
        ep_id = ep["Id"]
        ep_name = ep["Name"]
        public_url = ep.get("PublicURL", "localhost")

        print(f"Scanning endpoint {ep_name} (ID {ep_id})")

        containers = client.get_containers(ep_id)

        records = [
            build_service_record(c, public_url)
            for c in containers
        ]

        inventory.append({
            "endpoint_id": ep_id,
            "endpoint_name": ep_name,
            "containers": records
        })

    save_json(inventory)
    save_table(inventory)

    print("Done.")


if __name__ == "__main__":
    main()
