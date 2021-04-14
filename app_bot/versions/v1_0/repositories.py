import random
import re

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

from app_bot.enums import TelegramBotNotificationType
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
    @staticmethod
    def get_intents():
        # Темы, на которые бот может отвечать
        prepared_intents = []

        for intent in Intent.support.all():
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

        snowball = SnowballStemmer(language='russian')

        words = list(
            map(
                lambda y, s=snowball: s.stem(y),
                filter(lambda x, stop=stop_words: x not in stop, words)
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

            request_words_normal = cls.normalize_text(request_variant)  # Нормализуем слова в варианте запроса у темы

            common_words_count = len(set(request_words_normal).intersection(text_words_normal))  # Количество общих слов

            if common_words_count > suitable_request_common_words_count:
                suitable_request_common_words_count = common_words_count
                suitable_request_variant_words_count = len(request_words_normal)

        if suitable_request_variant_words_count:
            relevancy = suitable_request_common_words_count / suitable_request_variant_words_count

        return {
            'relevancy': relevancy,
            **intent
        }

    @classmethod
    def process_human_language(cls, text):
        # Обработка пользовательского ввода
        found_intent = None  # Бот пока не нашел подходящей темы
        _MIN_INTENT_RELEVANCY = 0.5  # Минимальная релевантность темы для данного текста

        processed_intents = []

        for intent in cls.get_intents():
            processed_intents.append(cls.calculate_intent_relevancy(intent, text))

        found_intents = sorted(
            list(filter(lambda x, min_rlv=_MIN_INTENT_RELEVANCY: x['relevancy'] >= min_rlv, processed_intents)),
            key=lambda x: x['relevancy'],
            reverse=True
        )

        if found_intents:
            found_intent = found_intents[0]

        return found_intent

    @classmethod
    def get_response(cls, text):
        intent = cls.process_human_language(text)

        if intent:
            return random.choice(intent['response'])

        return 'Не знаю, что на это ответить'
