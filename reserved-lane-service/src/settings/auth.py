from pydantic import BaseModel, PositiveInt


class AuthSettings(BaseModel):
    client_id: str
    audience: str = "account"
    server_uri: str
    internal_server_uri: str
    issuer: str | list[str]
    signature_cache_ttl: PositiveInt = 3600
    role: str = "reserved-lane-access"
    realm: str
