from django.contrib import admin
from django.urls import include,path
from exchange.views import landing,health
urlpatterns=[path("",landing),path("health/",health),path("admin/",admin.site.urls),path("api/v1/",include("exchange.urls"))]
