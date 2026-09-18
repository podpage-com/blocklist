from django.urls import path
from .views import ObservationListCreate,SyncView,IpDetail,ChangeFeed
urlpatterns=[path("observations/",ObservationListCreate.as_view()),path("observations/sync/",SyncView.as_view()),path("ips/<str:ip>/",IpDetail.as_view()),path("changes/",ChangeFeed.as_view())]
