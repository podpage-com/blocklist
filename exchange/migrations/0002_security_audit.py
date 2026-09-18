import secrets
from django.db import migrations,models
import django.db.models.deletion
def add_ids(apps,schema_editor):
    Org=apps.get_model("exchange","Organization")
    for o in Org.objects.all():
        o.public_id=secrets.token_urlsafe(16); o.save(update_fields=["public_id"])
class Migration(migrations.Migration):
    dependencies=[("exchange","0001_initial")]
    operations=[
      migrations.AddField(model_name="organization",name="public_id",field=models.CharField(blank=True,max_length=24,null=True,unique=True)),
      migrations.RunPython(add_ids,migrations.RunPython.noop),
      migrations.AlterField(model_name="organization",name="public_id",field=models.CharField(editable=False,max_length=24,unique=True)),
      migrations.CreateModel(name="ObservationEvent",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("action",models.CharField(choices=[("upsert","Upsert"),("deactivate","Deactivate")],max_length=16)),
        ("snapshot",models.JSONField()),("created_at",models.DateTimeField(auto_now_add=True,db_index=True)),
        ("observation",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="events",to="exchange.observation")),
        ("organization",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="observation_events",to="exchange.organization"))]),
      migrations.AddIndex(model_name="observationevent",index=models.Index(fields=["created_at","id"],name="exchange_ev_created_idx")),
    ]
