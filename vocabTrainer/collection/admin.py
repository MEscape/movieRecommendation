from django.contrib import admin
from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from .models import Collection, CollectionCombination
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse

User = get_user_model()

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'Germany')
]

class TableWidget(forms.Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language_dict = dict(LANGUAGE_CHOICES)

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the field as a table, with dynamic headers for the languages and actions to add/edit/delete rows.
        """
        if value is None:
            value = []

        if value:
            word_combination = value[0]
            word1_language_full = self.language_dict.get(word_combination['word1_language'], word_combination['word1_language'])
            word2_language_full = self.language_dict.get(word_combination['word2_language'], word_combination['word2_language'])
        else:
            word1_language_full = 'Word 1'
            word2_language_full = 'Word 2'

        table_html = render_to_string(
            'table_widget.html',
            {
                'word1_language_full': word1_language_full,
                'word2_language_full': word2_language_full,
                'value': value
            }
        )

        return mark_safe(table_html)

class TableField(forms.Field):
    def __init__(self, *args, **kwargs):
        widget = kwargs.pop('widget', TableWidget)
        super().__init__(*args, **kwargs, widget=widget)

class CollectionForm(forms.ModelForm):
    creator = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label="Creator",
        empty_label="Select a Creator",
        to_field_name="username"
    )
    word1_language = forms.ChoiceField(
        choices=[('', 'Select a Language')] + LANGUAGE_CHOICES,
        required=True,
        label="Language 1"
    )
    word2_language = forms.ChoiceField(
        choices=[('', 'Select a Language')] + LANGUAGE_CHOICES,
        required=True,
        label="Language 2"
    )

    class Meta:
        model = Collection
        fields = ('name', 'description', 'creator', 'word1_language', 'word2_language', 'image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(self, 'user', None)

        if self.instance and self.instance.creator:
            self.fields['creator'].initial = self.instance.creator

        if self.instance and self.instance.language_combination:
            languages = self.instance.language_combination.split('-')
            if len(languages) == 2:
                self.fields['word1_language'].initial = languages[0]
                self.fields['word2_language'].initial = languages[1]

        if self.instance and self.instance.image:
            secure_url = reverse('secure_image', args=[self.instance.image])
            token = AccessToken.for_user(user) if user else None

            if secure_url and token:
                secure_image_url = f"{secure_url}?token={token}"
                self.fields['image'].help_text = mark_safe(f'<img id="image-preview" src="{secure_image_url}" width="200" height="auto" alt="Current Image" />')

    def clean(self):
        cleaned_data = super().clean()
        word1_language = cleaned_data.get('word1_language')
        word2_language = cleaned_data.get('word2_language')

        if word1_language == word2_language:
            raise forms.ValidationError("Both languages are same.")

        print(cleaned_data)

        return cleaned_data

class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'language_combination')
    search_fields = ('name', 'creator', 'language_combination')
    list_filter = ('language_combination',)
    form = CollectionForm

    class Meta:
        model = Collection
        fields = 'word_combinations'

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.user = None

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form

    def save_model(self, request, obj, form, change):
        """
        Override save_model to set language_combination based on selected word languages.
        """
        obj.language_combination = f"{form.cleaned_data['word1_language']}-{form.cleaned_data['word2_language']}"
        if form.cleaned_data.get('image'):
            obj.image = form.cleaned_data['image']
        super().save_model(request, obj, form, change)

class CollectionCombinationForm(forms.ModelForm):
    word_combinations_table = TableField()

    class Meta:
        model = CollectionCombination
        fields = ('word_combinations_table',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['word_combinations_table'].initial = self.get_word_combinations_data()

    def get_word_combinations_data(self):
        """
        Fetch the word combinations related to this collection.
        """
        word_combinations = self.instance.word_combinations.all()
        word_combinations_data = []

        for wc in word_combinations:
            word_combinations_data.append({
                'word1_language': wc.word1.language,
                'word1_word': wc.word1.word,
                'word2_language': wc.word2.language,
                'word2_word': wc.word2.word,
            })

        return word_combinations_data

class CollectionCombinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'language_combination')
    search_fields = ('name', 'creator', 'language_combination')
    list_filter = ('language_combination',)
    form = CollectionCombinationForm

admin.site.register(Collection, CollectionAdmin)
admin.site.register(CollectionCombination, CollectionCombinationAdmin)
