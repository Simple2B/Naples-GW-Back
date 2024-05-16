from pydantic import BaseModel, ConfigDict


# {
#   "http": {
#     "routers": {
#       "whoami": {
#         "rule": "PathPrefix(`/`)",
#         "service": "whoami"
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


class TraefikRoute(BaseModel):
    rule: str
    service: str

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
