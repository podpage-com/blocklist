from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import Observation
class ObservationSerializer(serializers.ModelSerializer):
    organization=serializers.CharField(source="organization.slug",read_only=True)
    class Meta:
        model=Observation
        fields=["id","organization","ip_address","reason","first_seen_at","last_seen_at","expires_at","active","metadata","created_at","updated_at"]
        read_only_fields=["id","organization","created_at","updated_at"]
    def validate(self,attrs):
        now=timezone.now()
        attrs.setdefault("first_seen_at",now); attrs.setdefault("last_seen_at",now)
        attrs.setdefault("expires_at",now+timedelta(days=settings.DEFAULT_OBSERVATION_TTL_DAYS))
        if attrs["last_seen_at"]<attrs["first_seen_at"]: raise serializers.ValidationError("last_seen_at cannot precede first_seen_at")
        return attrs
class SyncItemSerializer(serializers.Serializer):
    ip_address=serializers.IPAddressField()
    reason=serializers.ChoiceField(choices=Observation.Reason.choices,default=Observation.Reason.OTHER)
    first_seen_at=serializers.DateTimeField(required=False); last_seen_at=serializers.DateTimeField(required=False); expires_at=serializers.DateTimeField(required=False)
    metadata=serializers.JSONField(required=False,default=dict)
class SyncSerializer(serializers.Serializer):
    observations=SyncItemSerializer(many=True,allow_empty=True)
