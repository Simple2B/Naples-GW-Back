import requests
from fastapi import HTTPException
from naples import schemas as s
from naples.logger import log
from naples.config import config

CFG = config()


def check_main_domain(url: str) -> bool:
    return CFG.MAIN_DOMAIN in url


def get_subdomain_from_url(url: str) -> str | None:
    return url.replace(f".{CFG.MAIN_DOMAIN}", "")


def get_godaddy_api_headers():
    return {
        "Authorization": f"sso-key {CFG.GODADDY_API_KEY}:{CFG.GODADDY_API_SECRET}",
        "Content-Type": "application/json",
    }


def get_godaddy_api_url(router: str) -> str:
    return f"{CFG.GODADDY_API_URL}/domains/{CFG.MAIN_DOMAIN}/{router}"


def check_subdomain_existence(subdomain):
    headers = get_godaddy_api_headers()
    url = get_godaddy_api_url("records")

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    dns_records = response.json()

    if not dns_records:
        return False

    records = [
        s.DNSRecord(
            type=record["type"],
            name=record["name"],
            data=record["data"],
            ttl=record["ttl"],
        )
        for record in dns_records
    ]

    for record in records:
        if record.name == subdomain and record.type == "A":
            return True  # Subdomain found with type A record

    return False  # Subdomain not found or not of type A


def add_godaddy_dns_record(subdomain: str):
    # URL for the GoDaddy API to add a DNS record
    record = s.DNSRecord(
        type=CFG.RECORD_TYPE,
        name=subdomain,
        data=CFG.GODADDY_IP_ADDRESS,
        ttl=CFG.GO_DADDY_TTL,
    )

    url = get_godaddy_api_url("records")

    log(log.INFO, "[add_godaddy_dns_record] URL: [%s]", url)

    headers = get_godaddy_api_headers()

    res = check_subdomain_existence(record.name)

    if res:
        log(log.INFO, "Subdomain already exists")
        return

    # Payload for the API request
    payload = [
        {
            "type": record.type,
            "name": record.name,
            "data": record.data,
            "ttl": record.ttl,
        }
    ]

    log(log.DEBUG, "Payload: [%s]", payload)

    # Make the API request to add the DNS record
    response: requests.Response = requests.patch(url, json=payload, headers=headers)

    log(log.INFO, "Response: [%s]", response.text)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    log(log.INFO, "DNS record added successfully")

    return response


def delete_godaddy_dns_record(subdomain: str):
    # URL for the GoDaddy API to add a DNS record
    record = s.DNSRecord(
        type=CFG.RECORD_TYPE,
        name=subdomain,
        data=CFG.GODADDY_IP_ADDRESS,
        ttl=CFG.GO_DADDY_TTL,
    )

    url = get_godaddy_api_url("records")

    log(log.INFO, "[delete_godaddy_dns_record] URL: [%s]", url)

    headers = get_godaddy_api_headers()

    res = check_subdomain_existence(record.name)

    if not res:
        log(log.INFO, "Subdomain does not exist")
        return

    # Payload for the API request
    payload = [
        {
            "type": record.type,
            "name": record.name,
            "data": record.data,
            "ttl": record.ttl,
        }
    ]

    log(log.DEBUG, "Payload: [%s]", payload)

    # Make the API request to add the DNS record
    response: requests.Response = requests.delete(url, json=payload, headers=headers)

    log(log.INFO, "Response: [%s]", response.text)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    log(log.INFO, "DNS record deleted successfully")

    return response
