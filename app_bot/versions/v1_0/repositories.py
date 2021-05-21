import random
import re

from channels.db import database_sync_to_async
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

from app_bot.enums import TelegramBotNotificationType, ChatterBotIntentCode
from app_bot.models import BotChat, BotMessage, Intent


class TelegramBotRepository:
    @staticmethod
    def get_or_create_chat(chat_id, chat_type, chat_title, username, first_name, last_name):
        chat, created = BotChat.objects.get_or_create(
            defaults={
                'title': chat_title,
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            },
            chat_id=chat_id,
            type=chat_type
        )
        return chat

    @staticmethod
    def create_message(chat, **kwargs):
        return BotMessage.objects.create(
            chat=chat,
            **kwargs
        )

    @staticmethod
    def get_chats_by_notification_types(notification_types=TelegramBotNotificationType.DEBUG.value, approved=True):
        return BotChat.objects.filter(
            approved=approved,
            notification_types__contains=[notification_types]
        )


class ChatterBotRepository:
    _DEFAULT_BOT_ANSWER = 'Попробуйте переформулировать свой запрос'
    _MANY_INTENTS_FOUND = 'Найдено несколько подходящих тем'
    _INTENT_EMPTY_RESPONSE = 'Тема без вариантов ответов'

    @staticmethod
    def get_intents():
        # Темы, на которые бот может отвечать
        prepared_intents = []

        for intent in Intent.common.all():
            prepared_intents.append({
                'code': intent.code,
                'topic': intent.topic,
                'request': [req.text for req in intent.requests.all()],
                'response': [res.text for res in intent.responses.all()],
            })

        return prepared_intents

    @staticmethod
    def normalize_text(text):
        # Удаление слов паразитов, лишних символов, окончаний
        clean = re.sub(r'[^ a-z A-Z А-Я а-я Ёё 0-9]', " ", text)
        words = word_tokenize(clean)

        stop_words = stopwords.words('russian')
        # Оставляем слова да нет есть
        stop_words.remove('да')
        stop_words.remove('нет')
        stop_words.remove('есть')

        snowball = SnowballStemmer(language='russian')

        words = list(
            map(
                lambda y, s=snowball: s.stem(y),
                # words
                list(filter(lambda x, stop=stop_words: x not in stop, words))  # TODO пока отключим стопслова
            )
        )
        return words

    @classmethod
    def calculate_intent_relevancy(cls, intent, text):
        # Вычисление релевантности темы для текста

        relevancy = 0  # Итоговая релевантность
        suitable_request_variant_words_count = 0  # Количество слов в варианте запроса, наиболее подходящем к тексту
        suitable_request_common_words_count = 0  # Количество общих слов в тексте и варианте запроса

        text_words_normal = cls.normalize_text(text)  # Список нормализованных слов запроса

        for request_variant in intent['request']:

            # Нормализуем слова в варианте запроса у темы
            request_words_normal = cls.normalize_text(request_variant)

            # Количество общих слов
            common_words_count = len(set(request_words_normal).intersection(text_words_normal))

            # Если число общих слов для текущего варианта больше числа общих слов для подходящего варианта
            if common_words_count > suitable_request_common_words_count:
                suitable_request_common_words_count = common_words_count
                suitable_request_variant_words_count = len(request_words_normal)

            # Если фраза полностью совпала
            if common_words_count == len(text_words_normal) and len(text_words_normal) == len(request_words_normal):
                suitable_request_common_words_count = common_words_count
                suitable_request_variant_words_count = len(request_words_normal)
                break  # выходим из цикла

        if suitable_request_variant_words_count:
            relevancy = suitable_request_common_words_count / suitable_request_variant_words_count

        return {
            'relevancy': relevancy,
            **intent
        }

    @classmethod
    def process_human_language(cls, text):
        # Обработка пользовательского ввода

        # TODO подумать необходимо ли определнная реакция на мат и брань, если да,
        #  то добавить надстройку над INTENTS что пользователь матерится

        found_intent = None  # Бот пока не нашел подходящей темы
        _MIN_INTENT_RELEVANCY = 0.3  # Минимальная релевантность темы для данного текста

        processed_intents = []

        for intent in cls.get_intents():
            processed_intents.append(cls.calculate_intent_relevancy(intent, text))

        found_intents = sorted(
            list(filter(lambda x, min_rlv=_MIN_INTENT_RELEVANCY: x['relevancy'] >= min_rlv, processed_intents)),
            key=lambda x: x['relevancy'],
            reverse=True  # По убыванию
        )

        # if found_intents:
        #     found_intent = found_intents[0]  # Берем первую тему

        return found_intents

    @classmethod
    def get_random_response_from_intent(cls, intent):
        return random.choice(
            intent['response']
        ) if intent['response'] else cls._INTENT_EMPTY_RESPONSE

    @classmethod
    def get_response(cls, text):
        intents = cls.process_human_language(text)

        intent_response = cls._DEFAULT_BOT_ANSWER
        intent_code = None
        many_intents = None
        if intents and len(intents) == 1:
            intent_code = intents[0]['code']
            intent_response = cls.get_random_response_from_intent(intents[0])

        if intents and len(intents) > 1:
            # Если совпало больше 1 темы
            obscene = next(filter(lambda x: x['code'] == ChatterBotIntentCode.OBSCENE_LANGUAGE.value, intents), None)
            top_relevancy = list(filter(lambda x: x['relevancy'] == 1, intents))

            # Если среди тем есть с нецензурной лексикой, то выдавать эту тему
            if obscene:
                intent_code = obscene['code']
                intent_response = cls.get_random_response_from_intent(obscene)
            elif len(top_relevancy) == 1:
                # Если среди них есть тема с relevancy=1 а остальные ниже, то выдавать только с relevancy=1
                intent_code = top_relevancy[0]['code']
                intent_response = cls.get_random_response_from_intent(top_relevancy[0])
            else:
                many_intents = intents
                intent_response = cls._MANY_INTENTS_FOUND

        return many_intents, intent_code, intent_response

    @classmethod
    def get_response_by_intent_code(cls, code):
        intent = Intent.with_responses.get(code=code)
        responses = [resp.text for resp in intent.responses.all()]
        return random.choice(responses) if responses else cls._DEFAULT_BOT_ANSWER


class AsyncChatterBotRepository(ChatterBotRepository):

    @database_sync_to_async
    def get_response(self, text):
        return super().get_response(text)
