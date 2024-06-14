import requests
from fastapi import HTTPException
from naples import schemas as s
from naples.logger import log
from naples.config import config

CFG = config()


def check_subdomain_existence(subdomain, headers, url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    dns_records = response.json()

    if not dns_records:
        return False

    records = [
        s.DNSRecordOut(
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


def add_dns_record(subdomain: str):
    # URL for the GoDaddy API to add a DNS record

    record = s.DNSRecord(
        domain=CFG.MAIN_DOMAIN,
        subdomain=subdomain,
        record_type=CFG.RECORD_TYPE,
        ttl=CFG.GO_DADDY_TTL,
        value=CFG.GODADDY_IP_ADDRESS,
        api_url=CFG.GODADDY_API_URL,
        api_key=CFG.GODADDY_API_KEY,
        api_secret=CFG.GODADDY_API_SECRET,
    )

    url = f"{record.api_url}/domains/{record.domain}/records"

    log(log.INFO, "[add_dns_record] URL: [%s]", url)

    headers = {
        "Authorization": f"sso-key {record.api_key}:{record.api_secret}",
        "Content-Type": "application/json",
    }

    res = check_subdomain_existence(record.subdomain, headers, url)

    if res:
        log(log.INFO, "Subdomain already exists")
        return

    # Payload for the API request
    payload = [
        {
            "type": record.record_type,
            "name": record.subdomain,
            "data": record.value,
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
