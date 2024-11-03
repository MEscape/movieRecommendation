from django.contrib import admin
from django.db import transaction, IntegrityError
from .serializers import _delete_combination, _create_combination, _update_combination
from django import forms
from django.contrib import messages
from .models import WordCombination, DictionaryEntry

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'Germany')
]

class WordCombinationForm(forms.ModelForm):
    word1_text = forms.CharField(max_length=100, label="Word 1")
    word2_text = forms.CharField(max_length=100, label="Word 2")
    language1 = forms.ChoiceField(choices=LANGUAGE_CHOICES, label="Language 1")
    language2 = forms.ChoiceField(choices=LANGUAGE_CHOICES, label="Language 2")

    class Meta:
        model = WordCombination
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['word1_text'].initial = self.instance.word1.word
            self.fields['word2_text'].initial = self.instance.word2.word
            self.fields['language1'].initial = self.instance.word1.language
            self.fields['language2'].initial = self.instance.word2.language

    def clean(self):
        cleaned_data = super().clean()
        word1_text = cleaned_data.get('word1_text')
        word2_text = cleaned_data.get('word2_text')
        language1 = cleaned_data.get('language1')
        language2 = cleaned_data.get('language2')

        if not word1_text or not word2_text:
            raise forms.ValidationError("Both words are required.")

        if not language1 or not language2:
            raise forms.ValidationError("Both languages are required.")

        if language1 == language2:
            raise forms.ValidationError("Both languages are same.")

        return cleaned_data

def remove_default_message(request):
    storage = messages.get_messages(request)
    try:
        del storage._queued_messages[-1]
    except KeyError:
        pass
    return True


class WordCombinationAdmin(admin.ModelAdmin):
    list_display = ('word1__word', 'word2__word')
    search_fields = ('word1__word', 'word2__word')
    form = WordCombinationForm

    def response_add(self, request, obj, post_url_continue=None):
        """override"""
        response = super().response_add(request, obj, post_url_continue)
        remove_default_message(request)
        return response

    def response_delete(self, request, obj_display, obj_id):
        """override"""
        response = super().response_delete(request, obj_display, obj_id)
        remove_default_message(request)
        return response

    def response_change(self, request, obj):
        """override"""
        response = super().response_change(request, obj)
        remove_default_message(request)
        return response

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """
        Override save_model to use custom create logic for WordCombination.
        """
        try:
            validated_data = {
                'words': [
                    {'word': form.cleaned_data['word1_text'], 'language': form.cleaned_data['language1']},
                    {'word': form.cleaned_data['word2_text'], 'language': form.cleaned_data['language2']}
                ]
            }
            if change:
                _update_combination(obj, validated_data)
                messages.success(request, "Word combination and related entries updated successfully.")
            else:
                _create_combination(validated_data)
                messages.success(request, "Word combination and related entries created successfully.")
        except Exception as e:
            messages.error(request, e)

    @transaction.atomic
    def delete_model(self, request, obj):
        """
        Override delete_model to use custom delete logic for WordCombination.
        """
        try:
            _delete_combination(obj)

            messages.success(request, "Word combination and related entries deleted successfully.")
        except Exception as e:
            messages.error(request, e)

class DictionaryEntryAdmin(admin.ModelAdmin):
    list_display = ('word', 'language')
    search_fields = ('word', 'language')

    def has_add_permission(self, request):
        """Disable adding new DictionaryEntry."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable changing existing DictionaryEntry."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deleting existing DictionaryEntry."""
        return False

admin.site.register(DictionaryEntry, DictionaryEntryAdmin)
admin.site.register(WordCombination, WordCombinationAdmin)
