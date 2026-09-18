import hashlib,secrets
from django.db import models
from django.utils import timezone

class Organization(models.Model):
    name=models.CharField(max_length=200,unique=True)
    slug=models.SlugField(max_length=100,unique=True)
    public_id=models.CharField(max_length=24,unique=True,editable=False,default=lambda: secrets.token_urlsafe(16))
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class ApiKey(models.Model):
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="api_keys")
    name=models.CharField(max_length=100,default="default")
    prefix=models.CharField(max_length=12,db_index=True)
    key_hash=models.CharField(max_length=64,unique=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    last_used_at=models.DateTimeField(null=True,blank=True)
    @classmethod
    def issue(cls,organization,name="default"):
        raw="bl_"+secrets.token_urlsafe(32)
        obj=cls.objects.create(organization=organization,name=name,prefix=raw[:12],key_hash=hashlib.sha256(raw.encode()).hexdigest())
        return obj,raw
    @classmethod
    def authenticate(cls,raw):
        try: key=cls.objects.select_related("organization").get(key_hash=hashlib.sha256(raw.encode()).hexdigest(),is_active=True,organization__is_active=True)
        except cls.DoesNotExist: return None
        cls.objects.filter(pk=key.pk).update(last_used_at=timezone.now())
        return key
    def __str__(self): return f"{self.organization} / {self.name} / {self.prefix}…"

class Observation(models.Model):
    class Reason(models.TextChoices):
        SIGNUP_ABUSE="signup_abuse","Signup abuse"; SPAM="spam","Spam"; SCRAPING="scraping","Scraping"
        CREDENTIAL_ABUSE="credential_abuse","Credential abuse"; PAYMENT_FRAUD="payment_fraud","Payment fraud"; DDOS="ddos","DDoS"; OTHER="other","Other"
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="observations")
    ip_address=models.GenericIPAddressField()
    reason=models.CharField(max_length=32,choices=Reason.choices,default=Reason.OTHER)
    first_seen_at=models.DateTimeField(); last_seen_at=models.DateTimeField(); expires_at=models.DateTimeField()
    active=models.BooleanField(default=True); metadata=models.JSONField(default=dict,blank=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["organization","ip_address"],name="one_observation_per_org_ip")]
        indexes=[models.Index(fields=["ip_address","active"]),models.Index(fields=["updated_at","id"]),models.Index(fields=["expires_at"])]
    def __str__(self): return f"{self.organization}: {self.ip_address}"

class ObservationEvent(models.Model):
    class Action(models.TextChoices):
        UPSERT="upsert","Upsert"; DEACTIVATE="deactivate","Deactivate"
    observation=models.ForeignKey(Observation,on_delete=models.CASCADE,related_name="events")
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="observation_events")
    action=models.CharField(max_length=16,choices=Action.choices)
    snapshot=models.JSONField()
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    class Meta:
        indexes=[models.Index(fields=["created_at","id"])]
