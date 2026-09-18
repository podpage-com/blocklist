from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Organization,ApiKey,Observation

class ApiTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name="Acme",slug="acme")
        _,self.raw=ApiKey.issue(self.org)
        self.client=APIClient(); self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.raw}")
    def test_auth_required(self):
        self.client.credentials(); self.assertEqual(self.client.get("/api/v1/observations/").status_code,401)
    def test_create_and_read(self):
        r=self.client.post("/api/v1/observations/",{"ip_address":"203.0.113.42","reason":"spam"},format="json")
        self.assertEqual(r.status_code,201)
        self.assertEqual(self.client.get("/api/v1/ips/203.0.113.42/").data["active_reporters"],1)
    def test_active_cannot_be_client_controlled(self):
        r=self.client.post("/api/v1/observations/",{"ip_address":"203.0.113.42","reason":"spam","active":False},format="json")
        self.assertEqual(r.status_code,201); self.assertTrue(Observation.objects.get().active)
    def test_upsert_does_not_duplicate(self):
        for reason in ["spam","scraping"]: self.client.post("/api/v1/observations/",{"ip_address":"203.0.113.42","reason":reason},format="json")
        self.assertEqual(Observation.objects.count(),1); self.assertEqual(Observation.objects.get().reason,"scraping")
    def test_sync_deactivates_missing_and_change_feed_sees_it(self):
        now=timezone.now()
        Observation.objects.create(organization=self.org,ip_address="203.0.113.1",reason="spam",first_seen_at=now,last_seen_at=now,expires_at=now+timedelta(days=7))
        since=timezone.now()
        r=self.client.put("/api/v1/observations/sync/",{"observations":[{"ip_address":"203.0.113.2","reason":"spam"}]},format="json")
        self.assertEqual(r.status_code,200); self.assertFalse(Observation.objects.get(ip_address="203.0.113.1").active)
        r=self.client.get("/api/v1/changes/",{"since":since.isoformat()})
        self.assertTrue(any(x["ip_address"]=="203.0.113.1" and not x["active"] for x in r.data["changes"]))
    def test_expired_hidden(self):
        now=timezone.now()
        Observation.objects.create(organization=self.org,ip_address="203.0.113.9",reason="spam",first_seen_at=now-timedelta(days=2),last_seen_at=now-timedelta(days=2),expires_at=now-timedelta(days=1))
        self.assertEqual(self.client.get("/api/v1/ips/203.0.113.9/").data["active_reporters"],0)
    def test_invalid_ip_detail(self):
        self.assertEqual(self.client.get("/api/v1/ips/not-an-ip/").status_code,400)
    def test_expired_submission_rejected(self):
        r=self.client.post("/api/v1/observations/",{"ip_address":"203.0.113.42","reason":"spam","expires_at":(timezone.now()-timedelta(days=1)).isoformat()},format="json")
        self.assertEqual(r.status_code,400)
    def test_duplicate_sync_ips_rejected(self):
        payload={"observations":[{"ip_address":"203.0.113.2"},{"ip_address":"203.0.113.2"}]}
        self.assertEqual(self.client.put("/api/v1/observations/sync/",payload,format="json").status_code,400)
