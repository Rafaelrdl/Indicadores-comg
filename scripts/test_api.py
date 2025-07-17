from infrastructure import arkmeds_client
import requests

try:
    arkmeds_client.get_workorders()
except requests.HTTPError as exc:
    if exc.response.status_code == 404:
        raise SystemExit("Unexpected 404 from API") from exc
    if exc.response.status_code == 401:
        print("Received 401 - invalid credentials")
    else:
        raise
else:
    print("Request succeeded")
