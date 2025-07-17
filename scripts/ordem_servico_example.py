from infrastructure import arkmeds_client
import requests

try:
    arkmeds_client.get_ordens_servico(page_size=1)
except requests.HTTPError as exc:
    raise SystemExit(f"Unexpected status {exc.response.status_code}") from exc
else:
    print("Request succeeded")
