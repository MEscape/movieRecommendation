from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import serializers

from .exceptions import WordCombinationFormatException, WordCombinationAlreadyExistsException
from .models import DictionaryEntry, WordCombination

class DictionaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ['id', 'word', 'language']


def _cleanup_dictionary_entry(old_entry, related_name):
    """
    Delete the dictionary entry if it is no longer linked to any word combinations.
    """
    if old_entry and getattr(old_entry, related_name).count() == 0:
        old_entry.delete()


def _get_or_create_dictionary_entry(validated_data, ignore_existing=False):
    """
    Get or create dictionary entries for the words provided in validated data.

    Args:
        validated_data (dict): The validated data containing words.

    Returns:
        tuple: A tuple containing the two dictionary entries (word1_entry, word2_entry).

    Raises:
        WordCombinationFormatException: If the number of words is not exactly two.
    """
    words_data = validated_data.pop('words')

    if len(words_data) != 2:
        raise WordCombinationFormatException()

    word_entries = []
    for key, value in words_data.items():
        word_entry, _ = DictionaryEntry.objects.get_or_create(language=key, word=value)
        word_entries.append(word_entry)


    if not ignore_existing:
        existing_combination = WordCombination.objects.filter(
            (Q(word1=word_entries[0]) & Q(word2=word_entries[1])) |
            (Q(word1=word_entries[1]) & Q(word2=word_entries[0]))
        ).first()

        if existing_combination:
            raise WordCombinationAlreadyExistsException(combination_id=existing_combination.id)

    return sorted([word_entries[0], word_entries[1]], key=lambda word: word.id)

@transaction.atomic
def _update_combination(instance, validated_data, ignore_existing=False):
    """
    Update an existing word combination with new entries or link existing ones.

    Args:
        instance (WordCombination): The existing word combination instance to update.
        validated_data (dict): The validated data containing new word information.

    Returns:
        WordCombination: The updated word combination instance.
    """
    old_word1_entry = instance.word1
    old_word2_entry = instance.word2
    new_word1_entry, new_word2_entry = _get_or_create_dictionary_entry(validated_data, ignore_existing)

    instance.word1 = new_word1_entry
    instance.word2 = new_word2_entry

    try:
        instance.save()

        _cleanup_dictionary_entry(old_word1_entry, 'word1_entries')
        _cleanup_dictionary_entry(old_word2_entry, 'word2_entries')
    except IntegrityError as e:
        raise WordCombinationAlreadyExistsException()

    return instance

@transaction.atomic
def _create_combination(validated_data, ignore_existing=False):
    """
    Create a new word combination using validated data.

    Args:
        validated_data (dict): The validated data containing word information.

    Returns:
        WordCombination: The newly created word combination instance.

    Raises:
        WordCombinationExistsException: If a combination with the same words already exists.
    """
    word1_entry, word2_entry = _get_or_create_dictionary_entry(validated_data, ignore_existing=ignore_existing)

    try:
        if ignore_existing:
            combination, _ = WordCombination.objects.get_or_create(word1=word1_entry, word2=word2_entry)
            return combination

        return WordCombination.objects.create(word1=word1_entry, word2=word2_entry)
    except IntegrityError:
        raise WordCombinationAlreadyExistsException()

@transaction.atomic
def _delete_combination(instance):
    """
    Delete a word combination and its linked dictionary entries if they are not linked to other combinations.

    Args:
        instance (WordCombination): The word combination instance to delete.

    Raises:
        IntegrityError: If there is a database integrity issue during the delete operation.
    """
    word1_entry = instance.word1
    word2_entry = instance.word2

    try:
        instance.delete()

        _cleanup_dictionary_entry(word1_entry, 'word1_entries')
        _cleanup_dictionary_entry(word2_entry, 'word2_entries')
    except IntegrityError:
        raise WordCombinationAlreadyExistsException()

def get_representation(instance):
    """
    Helper function to customize the representation of a word combination
    using languages as keys.

    Args:
        instance (WordCombination): The word combination instance to represent.

    Returns:
        dict: The serialized representation with languages as keys.
    """
    word1_data = DictionaryEntrySerializer(instance.word1).data
    word2_data = DictionaryEntrySerializer(instance.word2).data

    language_key_1 = word1_data["language"]
    language_key_2 = word2_data["language"]

    return {
        "id": instance.id,
        language_key_1: word1_data["word"],
        language_key_2: word2_data["word"]
    }

class WordCombinationSerializer(serializers.ModelSerializer):
    words = serializers.DictField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = WordCombination
        fields = ['id', 'words']

    def create(self, validated_data):
        return _create_combination(validated_data)

    def to_representation(self, instance):
        return get_representation(instance)

class WordCombinationDetailSerializer(serializers.ModelSerializer):
    words = serializers.DictField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = WordCombination
        fields = ['id', 'words']

    def update(self, instance, validated_data):
        return _update_combination(instance, validated_data)

    def delete(self, instance):
        return _delete_combination(instance)

    def to_representation(self, instance):
        return get_representation(instance)