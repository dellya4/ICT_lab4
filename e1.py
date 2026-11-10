import requests


BASE = "http://127.0.0.1:5000"

stale = 0


for i in range(100):
    requests.post(
        f"{BASE}/counter/increment"
    )

    primary = requests.get(
        f"{BASE}/counter?from=primary"
    ).json()["value"]

    replica = requests.get(
        f"{BASE}/counter?from=replica"
    ).json()["value"]

    if primary != replica:
        stale += 1


print(
    "stale reads from the replica:",
    stale,
    "out of 100"
)