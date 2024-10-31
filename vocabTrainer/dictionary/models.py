from django.db import models

class DictionaryEntry(models.Model):
    word1 = models.CharField(max_length=100)
    word2 = models.CharField(max_length=100)

    class Meta:
        unique_together = ('word1', 'word2')

    def __str__(self):
        return f"{self.word1} - {self.word2}"
