from django.db import models

class DictionaryEntry(models.Model):
    word = models.CharField(max_length=100)
    language = models.CharField(max_length=50)

    def __str__(self):
        return self.word

class WordCombination(models.Model):
    word1 = models.ForeignKey(DictionaryEntry, related_name='word1_entries', on_delete=models.CASCADE)
    word2 = models.ForeignKey(DictionaryEntry, related_name='word2_entries', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('word1', 'word2')

    def __str__(self):
        return f"{self.word1.word} - {self.word2.word}"
