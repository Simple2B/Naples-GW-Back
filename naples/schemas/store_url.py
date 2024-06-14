from pydantic import BaseModel, ConfigDict


# {
#   "http": {
#     "routers": {
#       "whoami": {
#         "rule": "PathPrefix(`/`)",
#         "service": "whoami",
#         "tls": {
#           "certResolver": "le"
#         },
#       }
#     },
#     "services": {
#       "whoami": {
#         "loadBalancer": {
#           "servers": [
#             {
#               "url": "http://whoami"
#             }
#           ]
#         }
#       }
#     }
#   }
# }


class TraefikTLS(BaseModel):
    certResolver: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikRoute(BaseModel):
    rule: str
    service: str
    tls: TraefikTLS

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikServer(BaseModel):
    url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikLoadBalancer(BaseModel):
    servers: list[TraefikServer]

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikService(BaseModel):
    loadBalancer: TraefikLoadBalancer

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikHttp(BaseModel):
    routers: dict[str, TraefikRoute]
    services: dict[str, TraefikService]

    model_config = ConfigDict(
        from_attributes=True,
    )


class TraefikData(BaseModel):
    http: TraefikHttp

    model_config = ConfigDict(
        from_attributes=True,
    )


class DNSRecord(BaseModel):
    domain: str
    subdomain: str
    record_type: str = "A"
    ttl: int = 600
    value: str

    api_url: str
    api_key: str
    api_secret: str
