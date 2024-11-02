from django.urls import path
from .views import (
    DictionaryEntryView,
    WordCombinationView,
    WordCombinationDetailView
)

urlpatterns = [
    path('', DictionaryEntryView.as_view(), name='dictionary_entry'),
    path('combinations/', WordCombinationView.as_view(), name='word_combination'),
    path('combinations/<int:pk>/', WordCombinationDetailView.as_view(), name='word_combination_detail'),
]
