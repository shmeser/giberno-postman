import sys

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
                "names": {"name:en": "", "name:ru": ""},
                "native": "аҧсуа"
            },
            "aa": {
                "name": "Afar",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Afaraf"
            },
            "af": {
                "name": "Afrikaans",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Afrikaans"
            },
            "ak": {
                "name": "Akan",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Akan"
            },
            "sq": {
                "name": "Albanian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Shqip"
            },
            "am": {
                "name": "Amharic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "አማርኛ"
            },
            "ar": {
                "name": "Arabic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "العربية"
            },
            "an": {
                "name": "Aragonese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Aragonés"
            },
            "hy": {
                "name": "Armenian",
                "names": {"name:en": "Armenian", "name:ru": "Армянский"},
                "native": "Հայերեն"
            },
            "as": {
                "name": "Assamese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "অসমীয়া"
            },
            "av": {
                "name": "Avaric",
                "names": {"name:en": "", "name:ru": ""},
                "native": "авар мацӀ, магӀарул мацӀ"
            },
            "ae": {
                "name": "Avestan",
                "names": {"name:en": "", "name:ru": ""},
                "native": "avesta"
            },
            "ay": {
                "name": "Aymara",
                "names": {"name:en": "", "name:ru": ""},
                "native": "aymar aru"
            },
            "az": {
                "name": "Azerbaijani",
                "names": {"name:en": "", "name:ru": ""},
                "native": "azərbaycan dili"
            },
            "bm": {
                "name": "Bambara",
                "names": {"name:en": "", "name:ru": ""},
                "native": "bamanankan"
            },
            "ba": {
                "name": "Bashkir",
                "names": {"name:en": "", "name:ru": ""},
                "native": "башҡорт теле"
            },
            "eu": {
                "name": "Basque",
                "names": {"name:en": "", "name:ru": ""},
                "native": "euskara, euskera"
            },
            "be": {
                "name": "Belarusian",
                "names": {"name:en": "Belarusian", "name:ru": "Белорусский"},
                "native": "Беларуская"
            },
            "bn": {
                "name": "Bengali",
                "names": {"name:en": "", "name:ru": ""},
                "native": "বাংলা"
            },
            "bh": {
                "name": "Bihari",
                "names": {"name:en": "", "name:ru": ""},
                "native": "भोजपुरी"
            },
            "bi": {
                "name": "Bislama",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Bislama"
            },
            "bs": {
                "name": "Bosnian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "bosanski jezik"
            },
            "br": {
                "name": "Breton",
                "names": {"name:en": "", "name:ru": ""},
                "native": "brezhoneg"
            },
            "bg": {
                "name": "Bulgarian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "български език"
            },
            "my": {
                "name": "Burmese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ဗမာစာ"
            },
            "ca": {
                "name": "Catalan; Valencian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Català"
            },
            "ch": {
                "name": "Chamorro",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Chamoru"
            },
            "ce": {
                "name": "Chechen",
                "names": {"name:en": "", "name:ru": ""},
                "native": "нохчийн мотт"
            },
            "ny": {
                "name": "Chichewa; Chewa; Nyanja",
                "names": {"name:en": "", "name:ru": ""},
                "native": "chiCheŵa, chinyanja"
            },
            "zh": {
                "name": "Chinese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "中文 (Zhōngwén), 汉语, 漢語"
            },
            "cv": {
                "name": "Chuvash",
                "names": {"name:en": "", "name:ru": ""},
                "native": "чӑваш чӗлхи"
            },
            "kw": {
                "name": "Cornish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kernewek"
            },
            "co": {
                "name": "Corsican",
                "names": {"name:en": "", "name:ru": ""},
                "native": "corsu, lingua corsa"
            },
            "cr": {
                "name": "Cree",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ᓀᐦᐃᔭᐍᐏᐣ"
            },
            "hr": {
                "name": "Croatian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "hrvatski"
            },
            "cs": {
                "name": "Czech",
                "names": {"name:en": "", "name:ru": ""},
                "native": "česky, čeština"
            },
            "da": {
                "name": "Danish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "dansk"
            },
            "dv": {
                "name": "Divehi; Dhivehi; Maldivian;",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ދިވެހި"
            },
            "nl": {
                "name": "Dutch",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Nederlands, Vlaams"
            },
            "en": {
                "name": "English",
                "names": {"name:en": "English", "name:ru": "Английский"},
                "native": "English"
            },
            "eo": {
                "name": "Esperanto",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Esperanto"
            },
            "et": {
                "name": "Estonian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "eesti, eesti keel"
            },
            "ee": {
                "name": "Ewe",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Eʋegbe"
            },
            "fo": {
                "name": "Faroese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "føroyskt"
            },
            "fj": {
                "name": "Fijian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "vosa Vakaviti"
            },
            "fi": {
                "name": "Finnish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "suomi, suomen kieli"
            },
            "fr": {
                "name": "French",
                "names": {"name:en": "", "name:ru": ""},
                "native": "français, langue française"
            },
            "ff": {
                "name": "Fula; Fulah; Pulaar; Pular",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Fulfulde, Pulaar, Pular"
            },
            "gl": {
                "name": "Galician",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Galego"
            },
            "ka": {
                "name": "Georgian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ქართული"
            },
            "de": {
                "name": "German",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Deutsch"
            },
            "el": {
                "name": "Greek, Modern",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Ελληνικά"
            },
            "gn": {
                "name": "Guaraní",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Avañeẽ"
            },
            "gu": {
                "name": "Gujarati",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ગુજરાતી"
            },
            "ht": {
                "name": "Haitian; Haitian Creole",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kreyòl ayisyen"
            },
            "ha": {
                "name": "Hausa",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Hausa, هَوُسَ"
            },
            "he": {
                "name": "Hebrew",
                "names": {"name:en": "", "name:ru": ""},
                "native": "עברית"
            },
            "iw": {
                "name": "Hebrew",
                "names": {"name:en": "", "name:ru": ""},
                "native": "עברית"
            },
            "hz": {
                "name": "Herero",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Otjiherero"
            },
            "hi": {
                "name": "Hindi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "हिन्दी, हिंदी"
            },
            "ho": {
                "name": "Hiri Motu",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Hiri Motu"
            },
            "hu": {
                "name": "Hungarian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Magyar"
            },
            "ia": {
                "name": "Interlingua",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Interlingua"
            },
            "id": {
                "name": "Indonesian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Bahasa Indonesia"
            },
            "ie": {
                "name": "Interlingue",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Originally called Occidental; then Interlingue after WWII"
            },
            "ga": {
                "name": "Irish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Gaeilge"
            },
            "ig": {
                "name": "Igbo",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Asụsụ Igbo"
            },
            "ik": {
                "name": "Inupiaq",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Iñupiaq, Iñupiatun"
            },
            "io": {
                "name": "Ido",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Ido"
            },
            "is": {
                "name": "Icelandic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Íslenska"
            },
            "it": {
                "name": "Italian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Italiano"
            },
            "iu": {
                "name": "Inuktitut",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ᐃᓄᒃᑎᑐᑦ"
            },
            "ja": {
                "name": "Japanese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "日本語 (にほんご／にっぽんご)"
            },
            "jv": {
                "name": "Javanese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "basa Jawa"
            },
            "kl": {
                "name": "Kalaallisut, Greenlandic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "kalaallisut, kalaallit oqaasii"
            },
            "kn": {
                "name": "Kannada",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ಕನ್ನಡ"
            },
            "kr": {
                "name": "Kanuri",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kanuri"
            },
            "ks": {
                "name": "Kashmiri",
                "names": {"name:en": "", "name:ru": ""},
                "native": "कश्मीरी, كشميري‎"
            },
            "kk": {
                "name": "Kazakh",
                "names": {"name:en": "Kazakh", "name:ru": "Казахский"},
                "native": "Қазақ тілі"
            },
            "km": {
                "name": "Khmer",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ភាសាខ្មែរ"
            },
            "ki": {
                "name": "Kikuyu, Gikuyu",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Gĩkũyũ"
            },
            "rw": {
                "name": "Kinyarwanda",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Ikinyarwanda"
            },
            "ky": {
                "name": "Kirghiz",
                "names": {"name:en": "Kirghiz", "name:ru": "Киргизский"},
                "native": "кыргыз тили"
            },
            "kv": {
                "name": "Komi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "коми кыв"
            },
            "kg": {
                "name": "Kongo",
                "names": {"name:en": "", "name:ru": ""},
                "native": "KiKongo"
            },
            "ko": {
                "name": "Korean",
                "names": {"name:en": "Korean", "name:ru": "Корейский"},
                "native": "한국어 (韓國語), 조선말 (朝鮮語)"
            },
            "ku": {
                "name": "Kurdish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kurdî, كوردی‎"
            },
            "kj": {
                "name": "Kwanyama, Kuanyama",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kuanyama"
            },
            "la": {
                "name": "Latin",
                "names": {"name:en": "", "name:ru": ""},
                "native": "latine, lingua latina"
            },
            "lb": {
                "name": "Luxembourgish, Letzeburgesch",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Lëtzebuergesch"
            },
            "lg": {
                "name": "Luganda",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Luganda"
            },
            "li": {
                "name": "Limburgish, Limburgan, Limburger",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Limburgs"
            },
            "ln": {
                "name": "Lingala",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Lingála"
            },
            "lo": {
                "name": "Lao",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ພາສາລາວ"
            },
            "lt": {
                "name": "Lithuanian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "lietuvių kalba"
            },
            "lu": {
                "name": "Luba-Katanga",
                "names": {"name:en": "", "name:ru": ""},
                "native": ""
            },
            "lv": {
                "name": "Latvian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "latviešu valoda"
            },
            "gv": {
                "name": "Manx",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Gaelg, Gailck"
            },
            "mk": {
                "name": "Macedonian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "македонски јазик"
            },
            "mg": {
                "name": "Malagasy",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Malagasy fiteny"
            },
            "ms": {
                "name": "Malay",
                "names": {"name:en": "", "name:ru": ""},
                "native": "bahasa Melayu, بهاس ملايو‎"
            },
            "ml": {
                "name": "Malayalam",
                "names": {"name:en": "", "name:ru": ""},
                "native": "മലയാളം"
            },
            "mt": {
                "name": "Maltese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Malti"
            },
            "mi": {
                "name": "Māori",
                "names": {"name:en": "", "name:ru": ""},
                "native": "te reo Māori"
            },
            "mr": {
                "name": "Marathi (Marāṭhī)",
                "names": {"name:en": "", "name:ru": ""},
                "native": "मराठी"
            },
            "mh": {
                "name": "Marshallese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kajin M̧ajeļ"
            },
            "mn": {
                "name": "Mongolian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "монгол"
            },
            "na": {
                "name": "Nauru",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Ekakairũ Naoero"
            },
            "nv": {
                "name": "Navajo, Navaho",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Diné bizaad, Dinékʼehǰí"
            },
            "nb": {
                "name": "Norwegian Bokmål",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Norsk bokmål"
            },
            "nd": {
                "name": "North Ndebele",
                "names": {"name:en": "", "name:ru": ""},
                "native": "isiNdebele"
            },
            "ne": {
                "name": "Nepali",
                "names": {"name:en": "", "name:ru": ""},
                "native": "नेपाली"
            },
            "ng": {
                "name": "Ndonga",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Owambo"
            },
            "nn": {
                "name": "Norwegian Nynorsk",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Norsk nynorsk"
            },
            "no": {
                "name": "Norwegian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Norsk"
            },
            "ii": {
                "name": "Nuosu",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ꆈꌠ꒿ Nuosuhxop"
            },
            "nr": {
                "name": "South Ndebele",
                "names": {"name:en": "", "name:ru": ""},
                "native": "isiNdebele"
            },
            "oc": {
                "name": "Occitan",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Occitan"
            },
            "oj": {
                "name": "Ojibwe, Ojibwa",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ᐊᓂᔑᓈᐯᒧᐎᓐ"
            },
            "cu": {
                "name": "Old Church Slavonic, Church Slavic, Church Slavonic, Old Bulgarian, Old Slavonic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ѩзыкъ словѣньскъ"
            },
            "om": {
                "name": "Oromo",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Afaan Oromoo"
            },
            "or": {
                "name": "Oriya",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ଓଡ଼ିଆ"
            },
            "os": {
                "name": "Ossetian, Ossetic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ирон æвзаг"
            },
            "pa": {
                "name": "Panjabi, Punjabi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ਪੰਜਾਬੀ, پنجابی‎"
            },
            "pi": {
                "name": "Pāli",
                "names": {"name:en": "", "name:ru": ""},
                "native": "पाऴि"
            },
            "fa": {
                "name": "Persian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "فارسی"
            },
            "pl": {
                "name": "Polish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "polski"
            },
            "ps": {
                "name": "Pashto, Pushto",
                "names": {"name:en": "", "name:ru": ""},
                "native": "پښتو"
            },
            "pt": {
                "name": "Portuguese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Português"
            },
            "qu": {
                "name": "Quechua",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Runa Simi, Kichwa"
            },
            "rm": {
                "name": "Romansh",
                "names": {"name:en": "", "name:ru": ""},
                "native": "rumantsch grischun"
            },
            "rn": {
                "name": "Kirundi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "kiRundi"
            },
            "ro": {
                "name": "Romanian, Moldavian, Moldovan",
                "names": {"name:en": "", "name:ru": ""},
                "native": "română"
            },
            "ru": {
                "name": "Russian",
                "names": {"name:en": "Russian", "name:ru": "Русский"},
                "native": "русский язык"
            },
            "sa": {
                "name": "Sanskrit (Saṁskṛta)",
                "names": {"name:en": "", "name:ru": ""},
                "native": "संस्कृतम्"
            },
            "sc": {
                "name": "Sardinian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "sardu"
            },
            "sd": {
                "name": "Sindhi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "सिन्धी, سنڌي، سندھی‎"
            },
            "se": {
                "name": "Northern Sami",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Davvisámegiella"
            },
            "sm": {
                "name": "Samoan",
                "names": {"name:en": "", "name:ru": ""},
                "native": "gagana faa Samoa"
            },
            "sg": {
                "name": "Sango",
                "names": {"name:en": "", "name:ru": ""},
                "native": "yângâ tî sängö"
            },
            "sr": {
                "name": "Serbian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "српски језик"
            },
            "gd": {
                "name": "Scottish Gaelic; Gaelic",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Gàidhlig"
            },
            "sn": {
                "name": "Shona",
                "names": {"name:en": "", "name:ru": ""},
                "native": "chiShona"
            },
            "si": {
                "name": "Sinhala, Sinhalese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "සිංහල"
            },
            "sk": {
                "name": "Slovak",
                "names": {"name:en": "", "name:ru": ""},
                "native": "slovenčina"
            },
            "sl": {
                "name": "Slovene",
                "names": {"name:en": "", "name:ru": ""},
                "native": "slovenščina"
            },
            "so": {
                "name": "Somali",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Soomaaliga, af Soomaali"
            },
            "st": {
                "name": "Southern Sotho",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Sesotho"
            },
            "es": {
                "name": "Spanish; Castilian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "español, castellano"
            },
            "su": {
                "name": "Sundanese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Basa Sunda"
            },
            "sw": {
                "name": "Swahili",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Kiswahili"
            },
            "ss": {
                "name": "Swati",
                "names": {"name:en": "", "name:ru": ""},
                "native": "SiSwati"
            },
            "sv": {
                "name": "Swedish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "svenska"
            },
            "ta": {
                "name": "Tamil",
                "names": {"name:en": "", "name:ru": ""},
                "native": "தமிழ்"
            },
            "te": {
                "name": "Telugu",
                "names": {"name:en": "", "name:ru": ""},
                "native": "తెలుగు"
            },
            "tg": {
                "name": "Tajik",
                "names": {"name:en": "", "name:ru": ""},
                "native": "тоҷикӣ, toğikī, تاجیکی‎"
            },
            "th": {
                "name": "Thai",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ไทย"
            },
            "ti": {
                "name": "Tigrinya",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ትግርኛ"
            },
            "bo": {
                "name": "Tibetan Standard, Tibetan, Central",
                "names": {"name:en": "", "name:ru": ""},
                "native": "བོད་ཡིག"
            },
            "tk": {
                "name": "Turkmen",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Türkmen, Түркмен"
            },
            "tl": {
                "name": "Tagalog",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Wikang Tagalog"
            },
            "tn": {
                "name": "Tswana",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Setswana"
            },
            "to": {
                "name": "Tonga (Tonga Islands)",
                "names": {"name:en": "", "name:ru": ""},
                "native": "faka Tonga"
            },
            "tr": {
                "name": "Turkish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Türkçe"
            },
            "ts": {
                "name": "Tsonga",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Xitsonga"
            },
            "tt": {
                "name": "Tatar",
                "names": {"name:en": "", "name:ru": ""},
                "native": "татарча, tatarça, تاتارچا‎"
            },
            "tw": {
                "name": "Twi",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Twi"
            },
            "ty": {
                "name": "Tahitian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Reo Tahiti"
            },
            "ug": {
                "name": "Uighur",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Uyƣurqə, ئۇيغۇرچە‎"
            },
            "uk": {
                "name": "Ukrainian",
                "names": {"name:en": "Ukrainian", "name:ru": "Украинский"},
                "native": "українська"
            },
            "ur": {
                "name": "Urdu",
                "names": {"name:en": "", "name:ru": ""},
                "native": "اردو"
            },
            "uz": {
                "name": "Uzbek",
                "names": {"name:en": "", "name:ru": ""},
                "native": "zbek, Ўзбек, أۇزبېك‎"
            },
            "ve": {
                "name": "Venda",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Tshivenḓa"
            },
            "vi": {
                "name": "Vietnamese",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Tiếng Việt"
            },
            "vo": {
                "name": "Volapük",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Volapük"
            },
            "wa": {
                "name": "Walloon",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Walon"
            },
            "cy": {
                "name": "Welsh",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Cymraeg"
            },
            "wo": {
                "name": "Wolof",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Wollof"
            },
            "fy": {
                "name": "Western Frisian",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Frysk"
            },
            "xh": {
                "name": "Xhosa",
                "names": {"name:en": "", "name:ru": ""},
                "native": "isiXhosa"
            },
            "yi": {
                "name": "Yiddish",
                "names": {"name:en": "", "name:ru": ""},
                "native": "ייִדיש"
            },
            "yo": {
                "name": "Yoruba",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Yorùbá"
            },
            "za": {
                "name": "Zhuang, Chuang",
                "names": {"name:en": "", "name:ru": ""},
                "native": "Saɯ cueŋƅ, Saw cuengh"
            }
        }

        added_count = 0
        updated_count = 0

        for code, data in reader.items():
            result, created = Language.objects.update_or_create(defaults=data, **{'iso_code': code})
            if created:
                added_count += 1
            else:
                updated_count += 1

        sys.stdout.write(f"Language seeder finished successfully! Added - {added_count}, updated - {updated_count}")
