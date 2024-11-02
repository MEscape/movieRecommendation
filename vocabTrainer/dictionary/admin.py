from django.contrib import admin
from .models import DictionaryEntry, WordCombination

class DictionaryEntryAdmin(admin.ModelAdmin):
    list_display = ('word', 'language')
    search_fields = ('word', 'language')

class WordCombinationAdmin(admin.ModelAdmin):
    list_display = ('word1', 'word2')
    search_fields = ('word1__word', 'word2__word')

# Register your models here
admin.site.register(DictionaryEntry, DictionaryEntryAdmin)
admin.site.register(WordCombination, WordCombinationAdmin)