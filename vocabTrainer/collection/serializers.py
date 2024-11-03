from django.urls import reverse
from rest_framework import serializers

from .exceptions import WordCombinationAlreadyExistsException
from .models import Collection
from django.contrib.auth import get_user_model
from dictionary.serializers import _create_combination, WordCombinationSerializer

User = get_user_model()

class CollectionSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "name", "description", "creator", "image", "language_combination"]

    def create(self, validated_data):
        creator_username = self.context['request'].user.username
        validated_data['creator'] = creator_username

        collection = Collection.objects.create(**validated_data)
        return collection

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if instance.image and request:
            secure_image_url = request.build_absolute_uri(
                reverse('secure_image', kwargs={'image_path': instance.image.name})
            )
            representation['image'] = secure_image_url
        return representation

class CollectionDetailSerializer(serializers.ModelSerializer):
    combinations = serializers.ListField(
        child=WordCombinationSerializer(),
        write_only=True
    )

    class Meta:
        model = Collection
        fields = ['combinations']

    def create(self, validated_data):
        collection = self.context['collection']
        word_combinations = []

        for item in validated_data.pop('combinations'):
            combination = _create_combination(item, ignoreExisting=True)

            if collection.word_combinations.filter(id=combination.id).exists():
                raise WordCombinationAlreadyExistsException(combination_id=combination.id)

            collection.word_combinations.add(combination)
            word_combinations.append(combination)

        return word_combinations