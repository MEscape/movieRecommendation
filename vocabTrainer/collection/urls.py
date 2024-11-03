from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    CollectionView,
    CollectionDetailView
)

urlpatterns = [
    path('', CollectionView.as_view(), name='collection'),
    path('<int:pk>/', CollectionDetailView.as_view(), name='collection_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)