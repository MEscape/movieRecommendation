from django.db import models
from dictionary.models import WordCombination

class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    word_combinations = models.ManyToManyField(WordCombination, related_name='collections', blank=True)
    creator = models.CharField(max_length=50)
    image = models.ImageField(upload_to='collections/', blank=True, null=True)
    language_combination = models.CharField(max_length=50)