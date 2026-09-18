from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import ApiKey
class Principal:
    def __init__(self,organization): self.organization=organization; self.pk=organization.pk
    @property
    def is_authenticated(self): return True
class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self,request):
        header=request.headers.get("Authorization","")
        if not header.startswith("Api-Key "): return None
        key=ApiKey.authenticate(header[8:].strip())
        if not key: raise AuthenticationFailed("Invalid or revoked API key.")
        return Principal(key.organization),key
    def authenticate_header(self,request): return "Api-Key"
