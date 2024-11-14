from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from .exceptions import WordCombinationNotFoundException
from .serializers import DictionaryEntrySerializer, WordCombinationSerializer, WordCombinationDetailSerializer
from rest_framework.response import Response
from drf_yasg import openapi
from .models import DictionaryEntry, WordCombination
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class DictionaryEntryView(generics.ListAPIView):
    serializer_class = DictionaryEntrySerializer

    def get_queryset(self):
        queryset = DictionaryEntry.objects.all().order_by('id')

        lang = self.request.query_params.get('lang', None)
        if lang:
            queryset = queryset.filter(language=lang)

        return queryset

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: WordCombinationSerializer(many=True)},
        operation_summary='Retrieve entries',
        operation_description='Get a list of all entries.'
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)

        logger.info('Retrieving dictionary entries')
        return Response(serializer.data, status=status.HTTP_200_OK)

class WordCombinationView(generics.ListCreateAPIView):
    serializer_class = WordCombinationSerializer

    def get_queryset(self):
        queryset = WordCombination.objects.all().order_by('id')

        lang = self.request.query_params.get('lang', None)
        if lang:
            lang_parts = lang.split('-')
            if len(lang_parts) != 2: return []

            lang1, lang2 = lang_parts
            queryset = queryset.filter(
                (Q(word1__language=lang1) & Q(word2__language=lang2)) |
                (Q(word1__language=lang2) & Q(word2__language=lang1))
            )

        return queryset

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: WordCombinationSerializer(many=True)},
        operation_summary='Retrieve word combinations',
        operation_description='Get a list of all word combinations.'
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)

        logger.info('Retrieving word combinations')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=WordCombinationSerializer,
        responses={
            status.HTTP_201_CREATED: WordCombinationSerializer,
            status.HTTP_400_BAD_REQUEST: 'Bad request due to existing word combination or wrong format',
            status.HTTP_404_NOT_FOUND: 'Word combination not found'
        },
        operation_summary='Create a new word combination',
        operation_description='Add a new word combination to the dictionary.'
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info('Creating a new word combination')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class WordCombinationDetailView(generics.DestroyAPIView):
    serializer_class = WordCombinationDetailSerializer
    lookup_field = 'pk'

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: WordCombinationDetailSerializer,
            status.HTTP_400_BAD_REQUEST: 'Word combination exists or due to wrong formatting',
            status.HTTP_404_NOT_FOUND: 'Word combination not found'
        },
        operation_summary='Update a word combination',
        operation_description='Update an existing word combination.'
    )
    def put(self, request, *args, **kwargs):
        combination_id, word_combination = self.get_object()

        serializer = self.get_serializer(word_combination, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'Updating word combination with id {combination_id}')
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            status.HTTP_400_BAD_REQUEST: 'Word combination not found'
        },
        operation_summary='Delete a word combination',
        operation_description='Remove a word combination from the dictionary.'
    )
    def delete(self, request, *args, **kwargs):
        combination_id, word_combination = self.get_object()

        serializer = self.get_serializer()
        serializer.delete(word_combination)

        logger.info(f'Deleted word combination with id {combination_id}')
        return Response({'deleted_id': combination_id}, status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """Helper method to get the WordCombination instance by ID."""
        combination_id = self.kwargs.get('pk')

        try:
            word_combination = WordCombination.objects.get(pk=combination_id)
        except WordCombination.DoesNotExist:
            raise WordCombinationNotFoundException()

        return combination_id, word_combination