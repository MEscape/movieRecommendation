from rest_framework import generics
from .models import DictionaryEntry
from .serializers import DictionaryEntrySerializer

class DictionaryView(generics.ListCreateAPIView):
    queryset = DictionaryEntry.objects.all()
    serializer_class = DictionaryEntrySerializer

class DictionaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DictionaryEntry.objects.all()
    serializer_class = DictionaryEntrySerializer