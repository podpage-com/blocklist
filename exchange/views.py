from datetime import timedelta
import ipaddress
from django.conf import settings
from django.db import transaction
from django.db.models import Count,Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Observation,ObservationEvent
from .serializers import ObservationSerializer,SyncSerializer,EventSerializer

def landing(request): return render(request,"landing.html")
def health(request): return JsonResponse({"status":"ok"})
def snapshot(obj): return ObservationSerializer(obj).data
def record(obj,action): ObservationEvent.objects.create(observation=obj,organization=obj.organization,action=action,snapshot=snapshot(obj))

class ObservationListCreate(generics.ListCreateAPIView):
    serializer_class=ObservationSerializer; throttle_scope="read"
    def get_queryset(self):
        qs=Observation.objects.select_related("organization").filter(active=True,expires_at__gt=timezone.now()).order_by("-last_seen_at")
        ip=self.request.query_params.get("ip")
        if ip:
            try: ip=str(ipaddress.ip_address(ip))
            except ValueError: return qs.none()
            qs=qs.filter(ip_address=ip)
        if self.request.query_params.get("reason"): qs=qs.filter(reason=self.request.query_params["reason"])
        if self.request.query_params.get("reporter"): qs=qs.filter(organization__public_id=self.request.query_params["reporter"])
        return qs
    @transaction.atomic
    def create(self,request,*args,**kwargs):
        self.throttle_scope="write"; s=self.get_serializer(data=request.data); s.is_valid(raise_exception=True)
        obj,created=Observation.objects.update_or_create(organization=request.user.organization,ip_address=s.validated_data["ip_address"],defaults={**s.validated_data,"active":True})
        record(obj,ObservationEvent.Action.UPSERT)
        return Response(self.get_serializer(obj).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class SyncView(APIView):
    throttle_scope="sync"
    @transaction.atomic
    def put(self,request):
        s=SyncSerializer(data=request.data); s.is_valid(raise_exception=True); org=request.user.organization; now=timezone.now(); items=s.validated_data["observations"]; ips={str(x["ip_address"]) for x in items}
        removed=list(Observation.objects.filter(organization=org,active=True).exclude(ip_address__in=ips))
        for obj in removed:
            obj.active=False; obj.updated_at=now; obj.save(update_fields=["active","updated_at"]); record(obj,ObservationEvent.Action.DEACTIVATE)
        for item in items:
            d=dict(item); d.setdefault("first_seen_at",now); d.setdefault("last_seen_at",now); d.setdefault("expires_at",now+timedelta(days=settings.DEFAULT_OBSERVATION_TTL_DAYS)); d["active"]=True
            obj,_=Observation.objects.update_or_create(organization=org,ip_address=item["ip_address"],defaults=d); record(obj,ObservationEvent.Action.UPSERT)
        return Response({"upserted":len(items),"deactivated":len(removed)})

class IpDetail(APIView):
    throttle_scope="read"
    def get(self,request,ip):
        try: ip=str(ipaddress.ip_address(ip))
        except ValueError: return Response({"detail":"Invalid IP address."},status=400)
        qs=Observation.objects.select_related("organization").filter(ip_address=ip,active=True,expires_at__gt=timezone.now()).order_by("-last_seen_at")
        return Response({"ip_address":ip,"active_reporters":qs.values("organization_id").distinct().count(),"reasons":list(qs.values("reason").annotate(count=Count("id")).order_by("-count")),"observations":ObservationSerializer(qs,many=True).data})

class ChangeFeed(APIView):
    throttle_scope="read"
    def get(self,request):
        limit=min(max(int(request.query_params.get("limit","500")),1),1000)
        cursor=request.query_params.get("cursor"); raw=request.query_params.get("since")
        qs=ObservationEvent.objects.select_related("organization").order_by("created_at","id")
        if cursor:
            try:
                ts,sid=cursor.rsplit(",",1); dt=parse_datetime(ts); sid=int(sid)
                if not dt or timezone.is_naive(dt): raise ValueError
            except ValueError: return Response({"detail":"Invalid cursor."},status=400)
            qs=qs.filter(Q(created_at__gt=dt)|Q(created_at=dt,id__gt=sid))
        else:
            since=parse_datetime(raw) if raw else None
            if not since or timezone.is_naive(since): return Response({"detail":"Provide timezone-aware since, or cursor."},status=400)
            qs=qs.filter(created_at__gt=since)
        rows=list(qs[:limit+1]); has_more=len(rows)>limit; rows=rows[:limit]
        next_cursor=f"{rows[-1].created_at.isoformat()},{rows[-1].id}" if rows else cursor
        return Response({"generated_at":timezone.now(),"changes":EventSerializer(rows,many=True).data,"next_cursor":next_cursor,"has_more":has_more})
