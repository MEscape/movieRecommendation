from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from .exceptions import WordCombinationExistsException, WordCombinationFormatException, WordCombinationNotFoundException
from .models import DictionaryEntry, WordCombination

User = get_user_model()

class DictionaryAPIEndpointsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token))

        self.word_entry1 = DictionaryEntry.objects.create(word='hello', language='en')
        self.word_entry2 = DictionaryEntry.objects.create(word='world', language='en')
        self.word_entry3 = DictionaryEntry.objects.create(word='hola', language='es')
        self.word_entry4 = DictionaryEntry.objects.create(word='mundo', language='es')

        WordCombination.objects.create(word1=self.word_entry2, word2=self.word_entry3)
        self.word_combination2 = WordCombination.objects.create(word1=self.word_entry3, word2=self.word_entry4)
        self.word_combination = WordCombination.objects.create(word1=self.word_entry1, word2=self.word_entry3)

    def test_list_dictionary_entries(self):
        response = self.client.get(reverse('dictionary_entry'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_dictionary_entries_filtered_by_language(self):
        response = self.client.get(reverse('dictionary_entry'), {'lang': 'en'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('dictionary_entry'), {'lang': 'es'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_dictionary_entries_with_non_existent_language(self):
        response = self.client.get(reverse('dictionary_entry'), {'lang': 'fr'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_dictionary_entries_with_case_sensitive_language(self):
        response = self.client.get(reverse('dictionary_entry'), {'lang': 'EN'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_word_combination_with_existing_entries(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'},
                {'word': 'world', 'language': 'en'}
            ]
        }
        response = self.client.post(reverse('word_combination'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WordCombination.objects.count(), 4)

    def test_create_word_combination_with_one_existing_and_one_new_entry(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'},
                {'word': 'newword', 'language': 'en'}
            ]
        }
        response = self.client.post(reverse('word_combination'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WordCombination.objects.count(), 4)
        self.assertTrue(DictionaryEntry.objects.filter(word='newword', language='en').exists())

    def test_create_word_combination_with_both_new_entries(self):
        data = {
            'words': [
                {'word': 'newword1', 'language': 'en'},
                {'word': 'newword2', 'language': 'en'}
            ]
        }
        response = self.client.post(reverse('word_combination'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WordCombination.objects.count(), 4)
        self.assertTrue(DictionaryEntry.objects.filter(word='newword1', language='en').exists())
        self.assertTrue(DictionaryEntry.objects.filter(word='newword2', language='en').exists())

    def test_create_duplicate_word_combination(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'},
                {'word': 'world', 'language': 'en'}
            ]
        }

        self.client.post(reverse('word_combination'), data, format='json')
        response = self.client.post(reverse('word_combination'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_combination_with_invalid_format(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'}
            ]
        }
        response = self.client.post(reverse('word_combination'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_word_combinations(self):
        WordCombination.objects.create(word1=self.word_entry1, word2=self.word_entry2)
        response = self.client.get(reverse('word_combination'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_word_combinations_filtered_by_language_pair(self):
        response = self.client.get(reverse('word_combination'), {'lang': 'en-es'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('word_combination'), {'lang': 'es-en'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('word_combination'), {'lang': 'es-es'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_word_combinations_with_non_existent_language_pair(self):
        response = self.client.get(reverse('word_combination'), {'lang': 'fr-de'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_word_combinations_with_invalid_language_format(self):
        response = self.client.get(reverse('word_combination'), {'lang': 'en'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(reverse('word_combination'), {'lang': 'en-'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_update_combination_new_entries(self):
        data = {
            'words': [
                {'word': 'goodbye', 'language': 'en'},
                {'word': 'earth', 'language': 'en'}
            ]
        }
        response = self.client.put(reverse('word_combination_detail', args=[self.word_combination.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(DictionaryEntry.objects.count(), 5)

        self.word_combination.refresh_from_db()
        self.assertEqual(self.word_combination.word1.word, 'goodbye')
        self.assertEqual(self.word_combination.word2.word, 'earth')

    def test_update_combination_link_existing_entries(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'},
                {'word': 'earth', 'language': 'en'}
            ]
        }
        response = self.client.put(reverse('word_combination_detail', args=[self.word_combination.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.word_combination.refresh_from_db()
        self.assertEqual(self.word_combination.word1.word, 'hello')
        self.assertEqual(self.word_combination.word2.word, 'earth')

        self.assertEqual(DictionaryEntry.objects.filter(word='hola').count(), 1)

    def test_update_combination_link_existing_entries_delete(self):
        data = {
            'words': [
                {'word': 'hola', 'language': 'sp'},
                {'word': 'earth', 'language': 'en'}
            ]
        }
        response = self.client.put(reverse('word_combination_detail', args=[self.word_combination2.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.word_combination2.refresh_from_db()
        self.assertEqual(self.word_combination2.word1.word, 'hola')
        self.assertEqual(self.word_combination2.word2.word, 'earth')

        self.assertEqual(DictionaryEntry.objects.filter(word='mundo').count(), 0)

    def test_update_combination_existing_combination_conflict(self):
        WordCombination.objects.create(word1=self.word_entry1, word2=self.word_entry2)

        data = {
            'words': [
                {'word': 'hello', 'language': 'en'},
                {'word': 'world', 'language': 'en'}
            ]
        }

        response = self.client.put(reverse('word_combination_detail', args=[self.word_combination.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_combination_invalid_format(self):
        data = {
            'words': [
                {'word': 'hello', 'language': 'en'}
            ]
        }

        response = self.client.put(reverse('word_combination_detail', args=[self.word_combination.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_combination_removes_combination_only(self):
        WordCombination.objects.create(word1=self.word_entry1, word2=DictionaryEntry.objects.create(word='goodbye', language='en'))
        initial_dict_entry_count = DictionaryEntry.objects.count()

        response = self.client.delete(reverse('word_combination_detail', args=[self.word_combination.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(WordCombination.objects.count(), 3)
        self.assertEqual(DictionaryEntry.objects.count(), initial_dict_entry_count)

    def test_delete_combination_removes_combination_and_entries(self):
        other_entry1 = DictionaryEntry.objects.create(word='foo', language='en')
        other_entry2 = DictionaryEntry.objects.create(word='bar', language='en')
        word_combination = WordCombination.objects.create(word1=other_entry1, word2=other_entry2)

        initial_dict_entry_count = DictionaryEntry.objects.count() - 4
        response = self.client.delete(reverse('word_combination_detail', args=[word_combination.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WordCombination.objects.count(), 3)
        self.assertEqual(DictionaryEntry.objects.count() - 4, initial_dict_entry_count - 2)

    def test_get_object_not_found(self):
        non_existent_pk = 1
        url = reverse('word_combination_detail', args=[non_existent_pk])
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
