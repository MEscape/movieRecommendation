from django.db import transaction, IntegrityError
from django.urls import reverse
from rest_framework import serializers
import copy

from rest_framework_simplejwt.tokens import AccessToken

from .exceptions import WordCombinationAlreadyExistsException
from .models import Collection
from dictionary.serializers import (
    _create_combination,
    WordCombinationSerializer,
    _delete_combination,
    _update_combination,
    WordCombination
)

def _cleanup_word_combination(old_entry):
    """
    Delete the word combination if it is no longer linked to any collections.
    """
    if old_entry and old_entry.collections.count() == 1:
        _delete_combination(old_entry)

def _add_secure_image_url(representation, instance, request):
    """
    Adds the secure image URL to the representation if the image exists.
    """
    if instance.image and request:
        token = AccessToken.for_user(request.user)
        secure_image_url = request.build_absolute_uri(
            reverse('secure_image', kwargs={'image_path': instance.image.name})
        )
        representation['image'] = f'{secure_image_url}?token={token}'
    return representation

class CollectionSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "name", "description", "creator", "image", "language_combination"]

    def create(self, validated_data):
        """
        Create a new collection and assign the current user as the creator.

        Args:
            validated_data: The validated data for collection creation.

        Returns:
            Collection: The created collection instance.
        """
        creator_username = self.context['request'].user.username
        validated_data['creator'] = creator_username

        collection = Collection.objects.create(**validated_data)
        return collection

    def to_representation(self, instance):
        """
        Modify the representation of the collection to include a secure image URL.

        Args:
            instance: The collection instance to represent.

        Returns:
            dict: The serialized representation of the collection.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request')
        return _add_secure_image_url(representation, instance, request)

class CollectionDetailSerializer(serializers.ModelSerializer):
    word_combinations = serializers.ListField(
        child=WordCombinationSerializer(),
        write_only=True
    )

    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'creator', 'image', 'language_combination', 'word_combinations']

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a collection and associate word combinations with it.

        Args:
            validated_data: The validated data for collection creation.

        Returns:
            list: A list of word combinations that were added to the collection.

        Raises:
            WordCombinationAlreadyExistsException: If the word combination already exists in the collection.
        """
        collection = self.context['collection']

        word_combinations = []
        for item in validated_data.pop('word_combinations'):
            combination = _create_combination(item, ignore_existing=True)

            if collection.word_combinations.filter(id=combination.id).exists():
                raise WordCombinationAlreadyExistsException(combination_id=combination.id)

            collection.word_combinations.add(combination)
            word_combinations.append(combination)

        return word_combinations

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update an existing collection instance with new data.

        Args:
            instance: The existing collection instance to update.
            validated_data: The validated data for updating the collection.

        Returns:
            Collection: The updated collection instance.
        """
        validated_data.pop('word_combinations', None)
        creator_username = self.context['request'].user.username
        validated_data['creator'] = creator_username

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def delete(self, instance):
        """
        Delete a collection and its linked word combinations if they are not linked to other combinations.

        Args:
            instance (Collection): The collection instance to delete.

        Raises:
            IntegrityError: If there is a database integrity issue during the delete operation.
        """
        word_combinations = instance.word_combinations.all()

        try:
            instance.delete()

            for word_combination in word_combinations:
                _cleanup_word_combination(word_combination)
        except IntegrityError:
            raise WordCombinationAlreadyExistsException()

    def to_representation(self, instance):
        """
        Modify the representation of the collection to include a secure image URL.

        Args:
            instance: The collection instance to represent.

        Returns:
            dict: The serialized representation of the collection.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request')
        return _add_secure_image_url(representation, instance, request)

    def to_internal_value(self, data):
        """
        Override to_internal_value to handle the input as direct language-key pairs
        rather than a nested 'words' dictionary.
        """
        word_combinations = data.get("word_combinations", [])

        modified_combinations = []
        for word_combination in word_combinations:
            modified_combinations.append({"words": word_combination})

        data["word_combinations"] = modified_combinations
        return data

class CollectionCombinationDetailSerializer(serializers.ModelSerializer):
    words = serializers.DictField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = WordCombination
        fields = ['id', 'words']

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Updates word combination with validated data, handling many-to-many relationship.
        Raises exception if duplicate combination found.
        """
        word_combination = self.context['word_combination']

        try:
            new_word_combination = _update_combination(word_combination, validated_data, ignore_existing=True)

            instance.word_combinations.add(new_word_combination)
            instance.word_combinations.remove(word_combination)

            return new_word_combination
        except IntegrityError:
            raise WordCombinationAlreadyExistsException(word_combination.id)

    @transaction.atomic
    def delete(self, instance):
        """
        Deletes instance and performs cleanup; raises exception if deletion fails.
        """
        word_combination = copy.copy(instance)

        try:
            instance.delete()
            _cleanup_word_combination(word_combination)
        except IntegrityError:
            raise WordCombinationAlreadyExistsException()