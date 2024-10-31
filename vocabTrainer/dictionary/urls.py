from django.urls import path
from .views import DictionaryView, DictionaryDetailView

urlpatterns = [
    path('', DictionaryView.as_view(), name='dictionary'),
    path('<int:pk>/', DictionaryDetailView.as_view(), name='dictionary_detail'),
]
