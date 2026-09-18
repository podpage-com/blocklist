from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Observation
from .serializers import ObservationSerializer,SyncSerializer

def landing(request): return render(request,"landing.html")
def health(request): return JsonResponse({"status":"ok"})

class ObservationListCreate(generics.ListCreateAPIView):
    serializer_class=ObservationSerializer
    throttle_scope="read"
    def get_queryset(self):
        qs=Observation.objects.select_related("organization").filter(active=True,expires_at__gt=timezone.now()).order_by("-last_seen_at")
        for param,field in [("ip","ip_address"),("reason","reason"),("organization","organization__slug")]:
            value=self.request.query_params.get(param)
            if value: qs=qs.filter(**{field:value})
        return qs
    def create(self,request,*args,**kwargs):
        self.throttle_scope="write"
        s=self.get_serializer(data=request.data); s.is_valid(raise_exception=True)
        obj,created=Observation.objects.update_or_create(organization=request.user.organization,ip_address=s.validated_data["ip_address"],defaults={**s.validated_data,"active":True})
        return Response(self.get_serializer(obj).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class SyncView(APIView):
    throttle_scope="sync"
    @transaction.atomic
    def put(self,request):
        s=SyncSerializer(data=request.data); s.is_valid(raise_exception=True)
        org=request.user.organization; now=timezone.now(); items=s.validated_data["observations"]
        ips={str(x["ip_address"]) for x in items}
        deactivated=Observation.objects.filter(organization=org,active=True).exclude(ip_address__in=ips).update(active=False)
        for item in items:
            d=dict(item); d.setdefault("first_seen_at",now); d.setdefault("last_seen_at",now); d.setdefault("expires_at",now+timedelta(days=settings.DEFAULT_OBSERVATION_TTL_DAYS)); d["active"]=True
            Observation.objects.update_or_create(organization=org,ip_address=item["ip_address"],defaults=d)
        return Response({"upserted":len(items),"deactivated":deactivated})

class IpDetail(APIView):
    throttle_scope="read"
    def get(self,request,ip):
        qs=Observation.objects.select_related("organization").filter(ip_address=ip,active=True,expires_at__gt=timezone.now()).order_by("-last_seen_at")
        return Response({"ip_address":ip,"active_reporters":qs.values("organization_id").distinct().count(),"reasons":list(qs.values("reason").annotate(count=Count("id")).order_by("-count")),"observations":ObservationSerializer(qs,many=True).data})

class ChangeFeed(APIView):
    throttle_scope="read"
    def get(self,request):
        raw=request.query_params.get("since")
        since=parse_datetime(raw) if raw else None
        if not since: return Response({"detail":"since is required as ISO 8601."},status=400)
        qs=Observation.objects.select_related("organization").filter(updated_at__gt=since).order_by("updated_at")[:5000]
        return Response({"since":raw,"generated_at":timezone.now(),"changes":ObservationSerializer(qs,many=True).data})
