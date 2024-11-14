from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
import logging

from .exceptions import CollectionNotFoundException, WordCombinationOfCollectionNotFoundException
from .models import Collection
from .serializers import CollectionSerializer, CollectionDetailSerializer, CollectionCombinationDetailSerializer
from dictionary.serializers import WordCombinationSerializer

logger = logging.getLogger(__name__)

class CollectionView(generics.ListCreateAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        queryset = Collection.objects.all().order_by('id')

        lang = self.request.query_params.get('lang', None)
        if lang:
            lang_parts = lang.split('-')
            if len(lang_parts) != 2: return []

            reversed_lang = '-'.join(reversed(lang_parts))
            queryset = queryset.filter(
                Q(language_combination=lang) | Q(language_combination=reversed_lang)
            )

        return queryset

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CollectionSerializer(many=True)},
        operation_summary='Retrieve collections',
        operation_description='Get a list of all collections.'
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)

        logger.info('Retrieving collections')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=CollectionSerializer,
        responses={
            status.HTTP_201_CREATED: CollectionSerializer,
            status.HTTP_400_BAD_REQUEST: 'Bad request due to wrong format',
        },
        operation_summary='Create a new collection',
        operation_description='Add a new collection which can be filled with word combinations.'
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        collection = serializer.save()

        logger.info('Creating a new collection')
        return Response(self.get_serializer(collection).data, status=status.HTTP_201_CREATED)

class CollectionDetailView(generics.ListCreateAPIView):
    serializer_class = CollectionDetailSerializer
    lookup_field = 'pk'

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CollectionDetailSerializer(many=True)},
        operation_summary='Retrieve word combinations of a collection',
        operation_description='Get a list of all word combinations of a collection.'
    )
    def get(self, request, *args, **kwargs):
        collection_id, collection = self.get_object()

        queryset = collection.word_combinations.all().order_by('id')
        page = self.paginate_queryset(queryset)

        serializer = WordCombinationSerializer(page, many=True)

        logger.info(f'Retrieving word combinations of collections with id {collection_id}')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=CollectionDetailSerializer,
        responses={
            status.HTTP_201_CREATED: CollectionDetailSerializer,
            status.HTTP_400_BAD_REQUEST: 'Already exists or due to wrong formatting',
        },
        operation_summary='Create a new word combination for a collection',
        operation_description='Add a new word combination for a collection.'
    )
    def post(self, request, *args, **kwargs):
        collection_id, collection = self.get_object()

        serializer = self.get_serializer(data=request.data, context={'collection': collection})
        serializer.is_valid(raise_exception=True)
        word_combinations = serializer.save()

        logger.info(f'Saving new word combinations to collection with id {collection_id}')
        response_data = WordCombinationSerializer(word_combinations, many=True).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=CollectionDetailSerializer,
        responses={
            status.HTTP_200_OK: CollectionDetailSerializer,
            status.HTTP_400_BAD_REQUEST: 'Already exists or due to wrong formatting',
        },
        operation_summary='Update a collection',
        operation_description='Update all fields of a collection except for word_combinations.'
    )
    def put(self, request, *args, **kwargs):
        collection_id, collection = self.get_object()

        serializer = self.get_serializer(collection, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'Updating collection details with id {collection_id}')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='Successfully deleted the collection',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'deleted_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the deleted collection'),
                    }
                ),
            ),
            status.HTTP_404_NOT_FOUND: 'Collection not found'
        },
        operation_summary='Delete a collection',
        operation_description='Delete a collection and all its associated word combinations.'
    )
    def delete(self, request, *args, **kwargs):
        collection_id, collection = self.get_object()

        serializer = self.get_serializer()
        serializer.delete(collection)

        logger.info(f'Deleted collection with id {collection_id}')
        return Response({'deleted_id': collection_id}, status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """Helper method to get the Collection instance by ID."""
        collection_id = self.kwargs.get('pk')

        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            raise CollectionNotFoundException()

        return collection_id, collection

class CollectionCombinationDetailView(generics.DestroyAPIView):
    serializer_class = CollectionCombinationDetailSerializer
    lookup_field = 'pk'

    @swagger_auto_schema(
        request_body=CollectionCombinationDetailSerializer,
        responses={
            status.HTTP_200_OK: WordCombinationSerializer,
            status.HTTP_400_BAD_REQUEST: 'Bad request due to wrong format or existing',
            status.HTTP_404_NOT_FOUND: 'Not found'
        },
        operation_summary='Update a word combination in a collection',
        operation_description='Updates a specific word combination in a collection using its ID.'
    )
    def put(self, request, *args, **kwargs):
        word_combination, collection = self.get_object()

        serializer = self.get_serializer(
            collection,
            data=request.data,
            context={'word_combination': word_combination}
        )
        serializer.is_valid(raise_exception=True)
        word_combination = serializer.save()

        logger.info(f'Updating word combination with id {word_combination.id} of collection with id {collection.id}')
        response_data = WordCombinationSerializer(word_combination).data

        return Response(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='Successfully deleted the word combination',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'deleted_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the deleted word combination'),
                    }
                ),
            ),
            status.HTTP_404_NOT_FOUND: 'Word combination not found'
        },
        operation_summary='Delete a word combination from a collection',
        operation_description='Deletes a specific word combination from a collection using its ID.'
    )
    def delete(self, request, *args, **kwargs):
        word_combination, collection = self.get_object()

        serializer = self.get_serializer()
        serializer.delete(word_combination)

        logger.info(f'Deleted word combination with id {word_combination.id} of collection with id {collection.id}')
        return Response({'deleted_id': word_combination.id}, status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """Helper method to get the Collection instance and Word Combination by ID."""
        collection_id = self.kwargs.get('pk')
        word_combination_id = self.kwargs.get('word_combination_pk')

        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            raise CollectionNotFoundException()

        try:
            word_combination = collection.word_combinations.get(pk=word_combination_id)
        except collection.word_combinations.model.DoesNotExist:
            raise WordCombinationOfCollectionNotFoundException()


        return word_combination, collection