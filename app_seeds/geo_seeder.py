import sys

from django.db import IntegrityError

from app_geo.models import Language


class LanguagesSeeder:

    def create(self, refresh=False):
        if refresh is True:
            self.truncate_table()

        self.create_languages()

    # TRUNCATE TABLE
    @staticmethod
    def truncate_table():
        Language.objects.all().delete()
        sys.stdout.write("Truncate app_geo__languages table ... [OK]\n")

    # CREATE LANGUAGES
    @staticmethod
    def create_languages():
        """ Данные языков """
        reader = {
            "ab": {
                "name": "Abkhaz",
                "native": "аҧсуа"
            },
            "aa": {
                "name": "Afar",
                "native": "Afaraf"
            },
            "af": {
                "name": "Afrikaans",
                "native": "Afrikaans"
            },
            "ak": {
                "name": "Akan",
                "native": "Akan"
            },
            "sq": {
                "name": "Albanian",
                "native": "Shqip"
            },
            "am": {
                "name": "Amharic",
                "native": "አማርኛ"
            },
            "ar": {
                "name": "Arabic",
                "native": "العربية"
            },
            "an": {
                "name": "Aragonese",
                "native": "Aragonés"
            },
            "hy": {
                "name": "Armenian",
                "native": "Հայերեն"
            },
            "as": {
                "name": "Assamese",
                "native": "অসমীয়া"
            },
            "av": {
                "name": "Avaric",
                "native": "авар мацӀ, магӀарул мацӀ"
            },
            "ae": {
                "name": "Avestan",
                "native": "avesta"
            },
            "ay": {
                "name": "Aymara",
                "native": "aymar aru"
            },
            "az": {
                "name": "Azerbaijani",
                "native": "azərbaycan dili"
            },
            "bm": {
                "name": "Bambara",
                "native": "bamanankan"
            },
            "ba": {
                "name": "Bashkir",
                "native": "башҡорт теле"
            },
            "eu": {
                "name": "Basque",
                "native": "euskara, euskera"
            },
            "be": {
                "name": "Belarusian",
                "native": "Беларуская"
            },
            "bn": {
                "name": "Bengali",
                "native": "বাংলা"
            },
            "bh": {
                "name": "Bihari",
                "native": "भोजपुरी"
            },
            "bi": {
                "name": "Bislama",
                "native": "Bislama"
            },
            "bs": {
                "name": "Bosnian",
                "native": "bosanski jezik"
            },
            "br": {
                "name": "Breton",
                "native": "brezhoneg"
            },
            "bg": {
                "name": "Bulgarian",
                "native": "български език"
            },
            "my": {
                "name": "Burmese",
                "native": "ဗမာစာ"
            },
            "ca": {
                "name": "Catalan; Valencian",
                "native": "Català"
            },
            "ch": {
                "name": "Chamorro",
                "native": "Chamoru"
            },
            "ce": {
                "name": "Chechen",
                "native": "нохчийн мотт"
            },
            "ny": {
                "name": "Chichewa; Chewa; Nyanja",
                "native": "chiCheŵa, chinyanja"
            },
            "zh": {
                "name": "Chinese",
                "native": "中文 (Zhōngwén), 汉语, 漢語"
            },
            "cv": {
                "name": "Chuvash",
                "native": "чӑваш чӗлхи"
            },
            "kw": {
                "name": "Cornish",
                "native": "Kernewek"
            },
            "co": {
                "name": "Corsican",
                "native": "corsu, lingua corsa"
            },
            "cr": {
                "name": "Cree",
                "native": "ᓀᐦᐃᔭᐍᐏᐣ"
            },
            "hr": {
                "name": "Croatian",
                "native": "hrvatski"
            },
            "cs": {
                "name": "Czech",
                "native": "česky, čeština"
            },
            "da": {
                "name": "Danish",
                "native": "dansk"
            },
            "dv": {
                "name": "Divehi; Dhivehi; Maldivian;",
                "native": "ދިވެހި"
            },
            "nl": {
                "name": "Dutch",
                "native": "Nederlands, Vlaams"
            },
            "en": {
                "name": "English",
                "native": "English"
            },
            "eo": {
                "name": "Esperanto",
                "native": "Esperanto"
            },
            "et": {
                "name": "Estonian",
                "native": "eesti, eesti keel"
            },
            "ee": {
                "name": "Ewe",
                "native": "Eʋegbe"
            },
            "fo": {
                "name": "Faroese",
                "native": "føroyskt"
            },
            "fj": {
                "name": "Fijian",
                "native": "vosa Vakaviti"
            },
            "fi": {
                "name": "Finnish",
                "native": "suomi, suomen kieli"
            },
            "fr": {
                "name": "French",
                "native": "français, langue française"
            },
            "ff": {
                "name": "Fula; Fulah; Pulaar; Pular",
                "native": "Fulfulde, Pulaar, Pular"
            },
            "gl": {
                "name": "Galician",
                "native": "Galego"
            },
            "ka": {
                "name": "Georgian",
                "native": "ქართული"
            },
            "de": {
                "name": "German",
                "native": "Deutsch"
            },
            "el": {
                "name": "Greek, Modern",
                "native": "Ελληνικά"
            },
            "gn": {
                "name": "Guaraní",
                "native": "Avañeẽ"
            },
            "gu": {
                "name": "Gujarati",
                "native": "ગુજરાતી"
            },
            "ht": {
                "name": "Haitian; Haitian Creole",
                "native": "Kreyòl ayisyen"
            },
            "ha": {
                "name": "Hausa",
                "native": "Hausa, هَوُسَ"
            },
            "he": {
                "name": "Hebrew",
                "native": "עברית"
            },
            "iw": {
                "name": "Hebrew",
                "native": "עברית"
            },
            "hz": {
                "name": "Herero",
                "native": "Otjiherero"
            },
            "hi": {
                "name": "Hindi",
                "native": "हिन्दी, हिंदी"
            },
            "ho": {
                "name": "Hiri Motu",
                "native": "Hiri Motu"
            },
            "hu": {
                "name": "Hungarian",
                "native": "Magyar"
            },
            "ia": {
                "name": "Interlingua",
                "native": "Interlingua"
            },
            "id": {
                "name": "Indonesian",
                "native": "Bahasa Indonesia"
            },
            "ie": {
                "name": "Interlingue",
                "native": "Originally called Occidental; then Interlingue after WWII"
            },
            "ga": {
                "name": "Irish",
                "native": "Gaeilge"
            },
            "ig": {
                "name": "Igbo",
                "native": "Asụsụ Igbo"
            },
            "ik": {
                "name": "Inupiaq",
                "native": "Iñupiaq, Iñupiatun"
            },
            "io": {
                "name": "Ido",
                "native": "Ido"
            },
            "is": {
                "name": "Icelandic",
                "native": "Íslenska"
            },
            "it": {
                "name": "Italian",
                "native": "Italiano"
            },
            "iu": {
                "name": "Inuktitut",
                "native": "ᐃᓄᒃᑎᑐᑦ"
            },
            "ja": {
                "name": "Japanese",
                "native": "日本語 (にほんご／にっぽんご)"
            },
            "jv": {
                "name": "Javanese",
                "native": "basa Jawa"
            },
            "kl": {
                "name": "Kalaallisut, Greenlandic",
                "native": "kalaallisut, kalaallit oqaasii"
            },
            "kn": {
                "name": "Kannada",
                "native": "ಕನ್ನಡ"
            },
            "kr": {
                "name": "Kanuri",
                "native": "Kanuri"
            },
            "ks": {
                "name": "Kashmiri",
                "native": "कश्मीरी, كشميري‎"
            },
            "kk": {
                "name": "Kazakh",
                "native": "Қазақ тілі"
            },
            "km": {
                "name": "Khmer",
                "native": "ភាសាខ្មែរ"
            },
            "ki": {
                "name": "Kikuyu, Gikuyu",
                "native": "Gĩkũyũ"
            },
            "rw": {
                "name": "Kinyarwanda",
                "native": "Ikinyarwanda"
            },
            "ky": {
                "name": "Kirghiz, Kyrgyz",
                "native": "кыргыз тили"
            },
            "kv": {
                "name": "Komi",
                "native": "коми кыв"
            },
            "kg": {
                "name": "Kongo",
                "native": "KiKongo"
            },
            "ko": {
                "name": "Korean",
                "native": "한국어 (韓國語), 조선말 (朝鮮語)"
            },
            "ku": {
                "name": "Kurdish",
                "native": "Kurdî, كوردی‎"
            },
            "kj": {
                "name": "Kwanyama, Kuanyama",
                "native": "Kuanyama"
            },
            "la": {
                "name": "Latin",
                "native": "latine, lingua latina"
            },
            "lb": {
                "name": "Luxembourgish, Letzeburgesch",
                "native": "Lëtzebuergesch"
            },
            "lg": {
                "name": "Luganda",
                "native": "Luganda"
            },
            "li": {
                "name": "Limburgish, Limburgan, Limburger",
                "native": "Limburgs"
            },
            "ln": {
                "name": "Lingala",
                "native": "Lingála"
            },
            "lo": {
                "name": "Lao",
                "native": "ພາສາລາວ"
            },
            "lt": {
                "name": "Lithuanian",
                "native": "lietuvių kalba"
            },
            "lu": {
                "name": "Luba-Katanga",
                "native": ""
            },
            "lv": {
                "name": "Latvian",
                "native": "latviešu valoda"
            },
            "gv": {
                "name": "Manx",
                "native": "Gaelg, Gailck"
            },
            "mk": {
                "name": "Macedonian",
                "native": "македонски јазик"
            },
            "mg": {
                "name": "Malagasy",
                "native": "Malagasy fiteny"
            },
            "ms": {
                "name": "Malay",
                "native": "bahasa Melayu, بهاس ملايو‎"
            },
            "ml": {
                "name": "Malayalam",
                "native": "മലയാളം"
            },
            "mt": {
                "name": "Maltese",
                "native": "Malti"
            },
            "mi": {
                "name": "Māori",
                "native": "te reo Māori"
            },
            "mr": {
                "name": "Marathi (Marāṭhī)",
                "native": "मराठी"
            },
            "mh": {
                "name": "Marshallese",
                "native": "Kajin M̧ajeļ"
            },
            "mn": {
                "name": "Mongolian",
                "native": "монгол"
            },
            "na": {
                "name": "Nauru",
                "native": "Ekakairũ Naoero"
            },
            "nv": {
                "name": "Navajo, Navaho",
                "native": "Diné bizaad, Dinékʼehǰí"
            },
            "nb": {
                "name": "Norwegian Bokmål",
                "native": "Norsk bokmål"
            },
            "nd": {
                "name": "North Ndebele",
                "native": "isiNdebele"
            },
            "ne": {
                "name": "Nepali",
                "native": "नेपाली"
            },
            "ng": {
                "name": "Ndonga",
                "native": "Owambo"
            },
            "nn": {
                "name": "Norwegian Nynorsk",
                "native": "Norsk nynorsk"
            },
            "no": {
                "name": "Norwegian",
                "native": "Norsk"
            },
            "ii": {
                "name": "Nuosu",
                "native": "ꆈꌠ꒿ Nuosuhxop"
            },
            "nr": {
                "name": "South Ndebele",
                "native": "isiNdebele"
            },
            "oc": {
                "name": "Occitan",
                "native": "Occitan"
            },
            "oj": {
                "name": "Ojibwe, Ojibwa",
                "native": "ᐊᓂᔑᓈᐯᒧᐎᓐ"
            },
            "cu": {
                "name": "Old Church Slavonic, Church Slavic, Church Slavonic, Old Bulgarian, Old Slavonic",
                "native": "ѩзыкъ словѣньскъ"
            },
            "om": {
                "name": "Oromo",
                "native": "Afaan Oromoo"
            },
            "or": {
                "name": "Oriya",
                "native": "ଓଡ଼ିଆ"
            },
            "os": {
                "name": "Ossetian, Ossetic",
                "native": "ирон æвзаг"
            },
            "pa": {
                "name": "Panjabi, Punjabi",
                "native": "ਪੰਜਾਬੀ, پنجابی‎"
            },
            "pi": {
                "name": "Pāli",
                "native": "पाऴि"
            },
            "fa": {
                "name": "Persian",
                "native": "فارسی"
            },
            "pl": {
                "name": "Polish",
                "native": "polski"
            },
            "ps": {
                "name": "Pashto, Pushto",
                "native": "پښتو"
            },
            "pt": {
                "name": "Portuguese",
                "native": "Português"
            },
            "qu": {
                "name": "Quechua",
                "native": "Runa Simi, Kichwa"
            },
            "rm": {
                "name": "Romansh",
                "native": "rumantsch grischun"
            },
            "rn": {
                "name": "Kirundi",
                "native": "kiRundi"
            },
            "ro": {
                "name": "Romanian, Moldavian, Moldovan",
                "native": "română"
            },
            "ru": {
                "name": "Russian",
                "native": "русский язык"
            },
            "sa": {
                "name": "Sanskrit (Saṁskṛta)",
                "native": "संस्कृतम्"
            },
            "sc": {
                "name": "Sardinian",
                "native": "sardu"
            },
            "sd": {
                "name": "Sindhi",
                "native": "सिन्धी, سنڌي، سندھی‎"
            },
            "se": {
                "name": "Northern Sami",
                "native": "Davvisámegiella"
            },
            "sm": {
                "name": "Samoan",
                "native": "gagana faa Samoa"
            },
            "sg": {
                "name": "Sango",
                "native": "yângâ tî sängö"
            },
            "sr": {
                "name": "Serbian",
                "native": "српски језик"
            },
            "gd": {
                "name": "Scottish Gaelic; Gaelic",
                "native": "Gàidhlig"
            },
            "sn": {
                "name": "Shona",
                "native": "chiShona"
            },
            "si": {
                "name": "Sinhala, Sinhalese",
                "native": "සිංහල"
            },
            "sk": {
                "name": "Slovak",
                "native": "slovenčina"
            },
            "sl": {
                "name": "Slovene",
                "native": "slovenščina"
            },
            "so": {
                "name": "Somali",
                "native": "Soomaaliga, af Soomaali"
            },
            "st": {
                "name": "Southern Sotho",
                "native": "Sesotho"
            },
            "es": {
                "name": "Spanish; Castilian",
                "native": "español, castellano"
            },
            "su": {
                "name": "Sundanese",
                "native": "Basa Sunda"
            },
            "sw": {
                "name": "Swahili",
                "native": "Kiswahili"
            },
            "ss": {
                "name": "Swati",
                "native": "SiSwati"
            },
            "sv": {
                "name": "Swedish",
                "native": "svenska"
            },
            "ta": {
                "name": "Tamil",
                "native": "தமிழ்"
            },
            "te": {
                "name": "Telugu",
                "native": "తెలుగు"
            },
            "tg": {
                "name": "Tajik",
                "native": "тоҷикӣ, toğikī, تاجیکی‎"
            },
            "th": {
                "name": "Thai",
                "native": "ไทย"
            },
            "ti": {
                "name": "Tigrinya",
                "native": "ትግርኛ"
            },
            "bo": {
                "name": "Tibetan Standard, Tibetan, Central",
                "native": "བོད་ཡིག"
            },
            "tk": {
                "name": "Turkmen",
                "native": "Türkmen, Түркмен"
            },
            "tl": {
                "name": "Tagalog",
                "native": "Wikang Tagalog"
            },
            "tn": {
                "name": "Tswana",
                "native": "Setswana"
            },
            "to": {
                "name": "Tonga (Tonga Islands)",
                "native": "faka Tonga"
            },
            "tr": {
                "name": "Turkish",
                "native": "Türkçe"
            },
            "ts": {
                "name": "Tsonga",
                "native": "Xitsonga"
            },
            "tt": {
                "name": "Tatar",
                "native": "татарча, tatarça, تاتارچا‎"
            },
            "tw": {
                "name": "Twi",
                "native": "Twi"
            },
            "ty": {
                "name": "Tahitian",
                "native": "Reo Tahiti"
            },
            "ug": {
                "name": "Uighur, Uyghur",
                "native": "Uyƣurqə, ئۇيغۇرچە‎"
            },
            "uk": {
                "name": "Ukrainian",
                "native": "українська"
            },
            "ur": {
                "name": "Urdu",
                "native": "اردو"
            },
            "uz": {
                "name": "Uzbek",
                "native": "zbek, Ўзбек, أۇزبېك‎"
            },
            "ve": {
                "name": "Venda",
                "native": "Tshivenḓa"
            },
            "vi": {
                "name": "Vietnamese",
                "native": "Tiếng Việt"
            },
            "vo": {
                "name": "Volapük",
                "native": "Volapük"
            },
            "wa": {
                "name": "Walloon",
                "native": "Walon"
            },
            "cy": {
                "name": "Welsh",
                "native": "Cymraeg"
            },
            "wo": {
                "name": "Wolof",
                "native": "Wollof"
            },
            "fy": {
                "name": "Western Frisian",
                "native": "Frysk"
            },
            "xh": {
                "name": "Xhosa",
                "native": "isiXhosa"
            },
            "yi": {
                "name": "Yiddish",
                "native": "ייִדיש"
            },
            "yo": {
                "name": "Yoruba",
                "native": "Yorùbá"
            },
            "za": {
                "name": "Zhuang, Chuang",
                "native": "Saɯ cueŋƅ, Saw cuengh"
            }
        }

        added_count = 0
        skipped = []

        for code, data in reader.items():
            language = Language()
            try:
                setattr(language, 'iso_code', code)
                for key, value in data.items():
                    setattr(language, key, value)
                language.save()
                added_count += 1
            except IntegrityError:
                skipped.append(Language.name)

        sys.stdout.write("Language seeder finished successfully! "
                         "Added - {}, skipped - {}\n".format(added_count, len(skipped)))
