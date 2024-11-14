from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    CollectionView,
    CollectionDetailView,
    CollectionCombinationDetailView
)

urlpatterns = [
    path('', CollectionView.as_view(), name='collection'),
    path('<int:pk>/', CollectionDetailView.as_view(), name='collection_detail'),
    path('<int:pk>/<int:word_combination_pk>/', CollectionCombinationDetailView.as_view(), name='collection_combination_detail'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)