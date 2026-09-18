import json
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import Observation

def validate_metadata(value):
    if len(json.dumps(value,separators=(",",":")).encode()) > settings.MAX_METADATA_BYTES:
        raise serializers.ValidationError(f"metadata must be <= {settings.MAX_METADATA_BYTES} bytes")
    return value

class ObservationSerializer(serializers.ModelSerializer):
    organization=serializers.CharField(source="organization.slug",read_only=True)
    metadata=serializers.JSONField(required=False,validators=[validate_metadata])
    class Meta:
        model=Observation
        fields=["id","organization","ip_address","reason","first_seen_at","last_seen_at","expires_at","active","metadata","created_at","updated_at"]
        read_only_fields=["id","organization","active","created_at","updated_at"]
    def validate(self,attrs):
        now=timezone.now()
        attrs.setdefault("first_seen_at",now); attrs.setdefault("last_seen_at",now)
        attrs.setdefault("expires_at",now+timedelta(days=settings.DEFAULT_OBSERVATION_TTL_DAYS))
        if attrs["last_seen_at"] < attrs["first_seen_at"]:
            raise serializers.ValidationError("last_seen_at cannot precede first_seen_at")
        if attrs["expires_at"] <= now:
            raise serializers.ValidationError("expires_at must be in the future")
        return attrs

class SyncItemSerializer(serializers.Serializer):
    ip_address=serializers.IPAddressField()
    reason=serializers.ChoiceField(choices=Observation.Reason.choices,default=Observation.Reason.OTHER)
    first_seen_at=serializers.DateTimeField(required=False)
    last_seen_at=serializers.DateTimeField(required=False)
    expires_at=serializers.DateTimeField(required=False)
    metadata=serializers.JSONField(required=False,default=dict,validators=[validate_metadata])
    def validate(self,attrs):
        now=timezone.now()
        if attrs.get("last_seen_at") and attrs.get("first_seen_at") and attrs["last_seen_at"] < attrs["first_seen_at"]:
            raise serializers.ValidationError("last_seen_at cannot precede first_seen_at")
        if attrs.get("expires_at") and attrs["expires_at"] <= now:
            raise serializers.ValidationError("expires_at must be in the future")
        return attrs

class SyncSerializer(serializers.Serializer):
    observations=SyncItemSerializer(many=True,allow_empty=True)
    def validate_observations(self,value):
        if len(value)>settings.MAX_SYNC_ITEMS:
            raise serializers.ValidationError(f"maximum {settings.MAX_SYNC_ITEMS} observations per sync")
        ips=[str(x["ip_address"]) for x in value]
        if len(ips)!=len(set(ips)):
            raise serializers.ValidationError("duplicate IP addresses are not allowed")
        return value
