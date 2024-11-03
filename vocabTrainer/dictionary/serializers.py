from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import serializers

from .exceptions import WordCombinationFormatException, WordCombinationIntegrityException, WordCombinationAlreadyExistsException
from .models import DictionaryEntry, WordCombination

class DictionaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ['id', 'word']


def _cleanup_dictionary_entry(old_entry, related_name):
    """
    Delete the dictionary entry if it is no longer linked to any word combinations.
    """
    if old_entry and getattr(old_entry, related_name).count() == 0:
        old_entry.delete()


def _get_or_create_dictionary_entry(validated_data, ignoreExisting=False):
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

    word1_data = words_data[0]
    word2_data = words_data[1]

    word1_entry, _ = DictionaryEntry.objects.get_or_create(**word1_data)
    word2_entry, _ = DictionaryEntry.objects.get_or_create(**word2_data)

    if not ignoreExisting:
        existing_combination = WordCombination.objects.filter(
            (Q(word1=word1_entry) & Q(word2=word2_entry)) |
            (Q(word1=word2_entry) & Q(word2=word1_entry))
        ).exists()

        if existing_combination:
            raise WordCombinationAlreadyExistsException(combination_id=existing_combination.id)

    return sorted([word1_entry, word2_entry], key=lambda word: word.id)

@transaction.atomic
def _update_combination(instance, validated_data):
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
    new_word1_entry, new_word2_entry = _get_or_create_dictionary_entry(validated_data)

    instance.word1 = new_word1_entry
    instance.word2 = new_word2_entry

    try:
        instance.save()

        _cleanup_dictionary_entry(old_word1_entry, 'word1_entries')
        _cleanup_dictionary_entry(old_word2_entry, 'word2_entries')
    except IntegrityError:
        raise WordCombinationIntegrityException()

    return instance

def _create_combination(validated_data, ignoreExisting=False):
    """
    Create a new word combination using validated data.

    Args:
        validated_data (dict): The validated data containing word information.

    Returns:
        WordCombination: The newly created word combination instance.

    Raises:
        WordCombinationExistsException: If a combination with the same words already exists.
    """
    word1_entry, word2_entry = _get_or_create_dictionary_entry(validated_data, ignoreExisting=ignoreExisting)

    try:
        if ignoreExisting:
            combination, _ = WordCombination.objects.get_or_create(word1=word1_entry, word2=word2_entry)
            return combination

        return WordCombination.objects.create(word1=word1_entry, word2=word2_entry)
    except IntegrityError:
        raise WordCombinationIntegrityException()

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
        raise WordCombinationIntegrityException()

class WordCombinationSerializer(serializers.ModelSerializer):
    words = serializers.ListField(child=serializers.DictField(), min_length=2, max_length=2, write_only=True)

    class Meta:
        model = WordCombination
        fields = ['id', 'words']

    def create(self, validated_data):
        return _create_combination(validated_data)

    def to_representation(self, instance):
        """
        Customize the representation of the word combination to include serialized word entries.

        Args:
            instance (WordCombination): The word combination instance to represent.

        Returns:
            dict: The serialized representation including detailed word information.
        """
        representation = super().to_representation(instance)
        representation['words'] = [
            DictionaryEntrySerializer(instance.word1).data,
            DictionaryEntrySerializer(instance.word2).data
        ]
        return representation

class WordCombinationDetailSerializer(serializers.ModelSerializer):
    words = serializers.ListField(child=serializers.DictField(), max_length=2, write_only=True)

    class Meta:
        model = WordCombination
        fields = ['id', 'words']

    def update(self, instance, validated_data):
        return _update_combination(instance, validated_data)

    def delete(self, instance):
        return _delete_combination(instance)

    def to_representation(self, instance):
        """
        Customize the representation of the word combination to include serialized word entries.

        Args:
            instance (WordCombination): The word combination instance to represent.

        Returns:
            dict: The serialized representation including detailed word information.
        """
        representation = super().to_representation(instance)
        representation['words'] = [
            DictionaryEntrySerializer(instance.word1).data,
            DictionaryEntrySerializer(instance.word2).data
        ]
        return representation