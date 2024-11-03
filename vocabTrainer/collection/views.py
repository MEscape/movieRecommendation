from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
import logging

from .exceptions import CollectionNotFoundException
from .models import Collection
from .serializers import CollectionSerializer, CollectionDetailSerializer
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
        _, collection = self.get_object()

        queryset = collection.word_combinations.all().order_by('id')
        page = self.paginate_queryset(queryset)

        serializer = WordCombinationSerializer(page, many=True)

        logger.info('Retrieving word combinations of collections')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=CollectionDetailSerializer,
        responses={
            status.HTTP_201_CREATED: CollectionDetailSerializer,
            status.HTTP_400_BAD_REQUEST: 'Bad request due to wrong format',
        },
        operation_summary='Create a new word combination for a collection',
        operation_description='Add a new word combination for a collection.'
    )
    def post(self, request, *args, **kwargs):
        _, collection = self.get_object()

        serializer = self.get_serializer(data=request.data, context={'collection': collection})
        serializer.is_valid(raise_exception=True)
        word_combinations = serializer.save()

        logger.info('Saving new word combinations to collection')
        response_data = WordCombinationSerializer(word_combinations, many=True).data

        return Response(response_data, status=status.HTTP_201_CREATED)


    def get_object(self):
        """Helper method to get the Collection instance by ID."""
        collection_id = self.kwargs.get('pk')

        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            raise CollectionNotFoundException()

        return collection_id, collection