import sys

from app_geo.models import Language


class LanguagesSeeder:
    
    NAME_EN = 'name:en'
    NAME_RU = 'name:ru'

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
    def create_languages(self):
        """ Данные языков """
        reader = {
            "ab": {
                "name": "Abkhaz",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "аҧсуа"
            },
            "aa": {
                "name": "Afar",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Afaraf"
            },
            "af": {
                "name": "Afrikaans",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Afrikaans"
            },
            "ak": {
                "name": "Akan",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Akan"
            },
            "sq": {
                "name": "Albanian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Shqip"
            },
            "am": {
                "name": "Amharic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "አማርኛ"
            },
            "ar": {
                "name": "Arabic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "العربية"
            },
            "an": {
                "name": "Aragonese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Aragonés"
            },
            "hy": {
                "name": "Armenian",
                "names": {self.NAME_EN: "Armenian", self.NAME_RU: "Армянский"},
                "native": "Հայերեն"
            },
            "as": {
                "name": "Assamese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "অসমীয়া"
            },
            "av": {
                "name": "Avaric",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "авар мацӀ, магӀарул мацӀ"
            },
            "ae": {
                "name": "Avestan",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "avesta"
            },
            "ay": {
                "name": "Aymara",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "aymar aru"
            },
            "az": {
                "name": "Azerbaijani",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "azərbaycan dili"
            },
            "bm": {
                "name": "Bambara",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "bamanankan"
            },
            "ba": {
                "name": "Bashkir",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "башҡорт теле"
            },
            "eu": {
                "name": "Basque",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "euskara, euskera"
            },
            "be": {
                "name": "Belarusian",
                "names": {self.NAME_EN: "Belarusian", self.NAME_RU: "Белорусский"},
                "native": "Беларуская"
            },
            "bn": {
                "name": "Bengali",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "বাংলা"
            },
            "bh": {
                "name": "Bihari",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "भोजपुरी"
            },
            "bi": {
                "name": "Bislama",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Bislama"
            },
            "bs": {
                "name": "Bosnian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "bosanski jezik"
            },
            "br": {
                "name": "Breton",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "brezhoneg"
            },
            "bg": {
                "name": "Bulgarian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "български език"
            },
            "my": {
                "name": "Burmese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ဗမာစာ"
            },
            "ca": {
                "name": "Catalan; Valencian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Català"
            },
            "ch": {
                "name": "Chamorro",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Chamoru"
            },
            "ce": {
                "name": "Chechen",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "нохчийн мотт"
            },
            "ny": {
                "name": "Chichewa; Chewa; Nyanja",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "chiCheŵa, chinyanja"
            },
            "zh": {
                "name": "Chinese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "中文 (Zhōngwén), 汉语, 漢語"
            },
            "cv": {
                "name": "Chuvash",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "чӑваш чӗлхи"
            },
            "kw": {
                "name": "Cornish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kernewek"
            },
            "co": {
                "name": "Corsican",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "corsu, lingua corsa"
            },
            "cr": {
                "name": "Cree",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ᓀᐦᐃᔭᐍᐏᐣ"
            },
            "hr": {
                "name": "Croatian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "hrvatski"
            },
            "cs": {
                "name": "Czech",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "česky, čeština"
            },
            "da": {
                "name": "Danish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "dansk"
            },
            "dv": {
                "name": "Divehi; Dhivehi; Maldivian;",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ދިވެހި"
            },
            "nl": {
                "name": "Dutch",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Nederlands, Vlaams"
            },
            "en": {
                "name": "English",
                "names": {self.NAME_EN: "English", self.NAME_RU: "Английский"},
                "native": "English"
            },
            "eo": {
                "name": "Esperanto",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Esperanto"
            },
            "et": {
                "name": "Estonian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "eesti, eesti keel"
            },
            "ee": {
                "name": "Ewe",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Eʋegbe"
            },
            "fo": {
                "name": "Faroese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "føroyskt"
            },
            "fj": {
                "name": "Fijian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "vosa Vakaviti"
            },
            "fi": {
                "name": "Finnish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "suomi, suomen kieli"
            },
            "fr": {
                "name": "French",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "français, langue française"
            },
            "ff": {
                "name": "Fula; Fulah; Pulaar; Pular",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Fulfulde, Pulaar, Pular"
            },
            "gl": {
                "name": "Galician",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Galego"
            },
            "ka": {
                "name": "Georgian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ქართული"
            },
            "de": {
                "name": "German",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Deutsch"
            },
            "el": {
                "name": "Greek, Modern",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Ελληνικά"
            },
            "gn": {
                "name": "Guaraní",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Avañeẽ"
            },
            "gu": {
                "name": "Gujarati",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ગુજરાતી"
            },
            "ht": {
                "name": "Haitian; Haitian Creole",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kreyòl ayisyen"
            },
            "ha": {
                "name": "Hausa",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Hausa, هَوُسَ"
            },
            "he": {
                "name": "Hebrew",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "עברית"
            },
            "iw": {
                "name": "Hebrew",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "עברית"
            },
            "hz": {
                "name": "Herero",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Otjiherero"
            },
            "hi": {
                "name": "Hindi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "हिन्दी, हिंदी"
            },
            "ho": {
                "name": "Hiri Motu",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Hiri Motu"
            },
            "hu": {
                "name": "Hungarian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Magyar"
            },
            "ia": {
                "name": "Interlingua",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Interlingua"
            },
            "id": {
                "name": "Indonesian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Bahasa Indonesia"
            },
            "ie": {
                "name": "Interlingue",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Originally called Occidental; then Interlingue after WWII"
            },
            "ga": {
                "name": "Irish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Gaeilge"
            },
            "ig": {
                "name": "Igbo",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Asụsụ Igbo"
            },
            "ik": {
                "name": "Inupiaq",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Iñupiaq, Iñupiatun"
            },
            "io": {
                "name": "Ido",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Ido"
            },
            "is": {
                "name": "Icelandic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Íslenska"
            },
            "it": {
                "name": "Italian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Italiano"
            },
            "iu": {
                "name": "Inuktitut",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ᐃᓄᒃᑎᑐᑦ"
            },
            "ja": {
                "name": "Japanese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "日本語 (にほんご／にっぽんご)"
            },
            "jv": {
                "name": "Javanese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "basa Jawa"
            },
            "kl": {
                "name": "Kalaallisut, Greenlandic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "kalaallisut, kalaallit oqaasii"
            },
            "kn": {
                "name": "Kannada",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ಕನ್ನಡ"
            },
            "kr": {
                "name": "Kanuri",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kanuri"
            },
            "ks": {
                "name": "Kashmiri",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "कश्मीरी, كشميري‎"
            },
            "kk": {
                "name": "Kazakh",
                "names": {self.NAME_EN: "Kazakh", self.NAME_RU: "Казахский"},
                "native": "Қазақ тілі"
            },
            "km": {
                "name": "Khmer",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ភាសាខ្មែរ"
            },
            "ki": {
                "name": "Kikuyu, Gikuyu",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Gĩkũyũ"
            },
            "rw": {
                "name": "Kinyarwanda",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Ikinyarwanda"
            },
            "ky": {
                "name": "Kirghiz",
                "names": {self.NAME_EN: "Kirghiz", self.NAME_RU: "Киргизский"},
                "native": "кыргыз тили"
            },
            "kv": {
                "name": "Komi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "коми кыв"
            },
            "kg": {
                "name": "Kongo",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "KiKongo"
            },
            "ko": {
                "name": "Korean",
                "names": {self.NAME_EN: "Korean", self.NAME_RU: "Корейский"},
                "native": "한국어 (韓國語), 조선말 (朝鮮語)"
            },
            "ku": {
                "name": "Kurdish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kurdî, كوردی‎"
            },
            "kj": {
                "name": "Kwanyama, Kuanyama",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kuanyama"
            },
            "la": {
                "name": "Latin",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "latine, lingua latina"
            },
            "lb": {
                "name": "Luxembourgish, Letzeburgesch",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Lëtzebuergesch"
            },
            "lg": {
                "name": "Luganda",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Luganda"
            },
            "li": {
                "name": "Limburgish, Limburgan, Limburger",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Limburgs"
            },
            "ln": {
                "name": "Lingala",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Lingála"
            },
            "lo": {
                "name": "Lao",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ພາສາລາວ"
            },
            "lt": {
                "name": "Lithuanian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "lietuvių kalba"
            },
            "lu": {
                "name": "Luba-Katanga",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": ""
            },
            "lv": {
                "name": "Latvian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "latviešu valoda"
            },
            "gv": {
                "name": "Manx",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Gaelg, Gailck"
            },
            "mk": {
                "name": "Macedonian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "македонски јазик"
            },
            "mg": {
                "name": "Malagasy",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Malagasy fiteny"
            },
            "ms": {
                "name": "Malay",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "bahasa Melayu, بهاس ملايو‎"
            },
            "ml": {
                "name": "Malayalam",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "മലയാളം"
            },
            "mt": {
                "name": "Maltese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Malti"
            },
            "mi": {
                "name": "Māori",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "te reo Māori"
            },
            "mr": {
                "name": "Marathi (Marāṭhī)",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "मराठी"
            },
            "mh": {
                "name": "Marshallese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kajin M̧ajeļ"
            },
            "mn": {
                "name": "Mongolian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "монгол"
            },
            "na": {
                "name": "Nauru",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Ekakairũ Naoero"
            },
            "nv": {
                "name": "Navajo, Navaho",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Diné bizaad, Dinékʼehǰí"
            },
            "nb": {
                "name": "Norwegian Bokmål",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Norsk bokmål"
            },
            "nd": {
                "name": "North Ndebele",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "isiNdebele"
            },
            "ne": {
                "name": "Nepali",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "नेपाली"
            },
            "ng": {
                "name": "Ndonga",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Owambo"
            },
            "nn": {
                "name": "Norwegian Nynorsk",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Norsk nynorsk"
            },
            "no": {
                "name": "Norwegian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Norsk"
            },
            "ii": {
                "name": "Nuosu",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ꆈꌠ꒿ Nuosuhxop"
            },
            "nr": {
                "name": "South Ndebele",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "isiNdebele"
            },
            "oc": {
                "name": "Occitan",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Occitan"
            },
            "oj": {
                "name": "Ojibwe, Ojibwa",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ᐊᓂᔑᓈᐯᒧᐎᓐ"
            },
            "cu": {
                "name": "Old Church Slavonic, Church Slavic, Church Slavonic, Old Bulgarian, Old Slavonic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ѩзыкъ словѣньскъ"
            },
            "om": {
                "name": "Oromo",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Afaan Oromoo"
            },
            "or": {
                "name": "Oriya",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ଓଡ଼ିଆ"
            },
            "os": {
                "name": "Ossetian, Ossetic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ирон æвзаг"
            },
            "pa": {
                "name": "Panjabi, Punjabi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ਪੰਜਾਬੀ, پنجابی‎"
            },
            "pi": {
                "name": "Pāli",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "पाऴि"
            },
            "fa": {
                "name": "Persian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "فارسی"
            },
            "pl": {
                "name": "Polish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "polski"
            },
            "ps": {
                "name": "Pashto, Pushto",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "پښتو"
            },
            "pt": {
                "name": "Portuguese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Português"
            },
            "qu": {
                "name": "Quechua",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Runa Simi, Kichwa"
            },
            "rm": {
                "name": "Romansh",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "rumantsch grischun"
            },
            "rn": {
                "name": "Kirundi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "kiRundi"
            },
            "ro": {
                "name": "Romanian, Moldavian, Moldovan",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "română"
            },
            "ru": {
                "name": "Russian",
                "names": {self.NAME_EN: "Russian", self.NAME_RU: "Русский"},
                "native": "русский язык"
            },
            "sa": {
                "name": "Sanskrit (Saṁskṛta)",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "संस्कृतम्"
            },
            "sc": {
                "name": "Sardinian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "sardu"
            },
            "sd": {
                "name": "Sindhi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "सिन्धी, سنڌي، سندھی‎"
            },
            "se": {
                "name": "Northern Sami",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Davvisámegiella"
            },
            "sm": {
                "name": "Samoan",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "gagana faa Samoa"
            },
            "sg": {
                "name": "Sango",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "yângâ tî sängö"
            },
            "sr": {
                "name": "Serbian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "српски језик"
            },
            "gd": {
                "name": "Scottish Gaelic; Gaelic",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Gàidhlig"
            },
            "sn": {
                "name": "Shona",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "chiShona"
            },
            "si": {
                "name": "Sinhala, Sinhalese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "සිංහල"
            },
            "sk": {
                "name": "Slovak",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "slovenčina"
            },
            "sl": {
                "name": "Slovene",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "slovenščina"
            },
            "so": {
                "name": "Somali",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Soomaaliga, af Soomaali"
            },
            "st": {
                "name": "Southern Sotho",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Sesotho"
            },
            "es": {
                "name": "Spanish; Castilian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "español, castellano"
            },
            "su": {
                "name": "Sundanese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Basa Sunda"
            },
            "sw": {
                "name": "Swahili",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Kiswahili"
            },
            "ss": {
                "name": "Swati",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "SiSwati"
            },
            "sv": {
                "name": "Swedish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "svenska"
            },
            "ta": {
                "name": "Tamil",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "தமிழ்"
            },
            "te": {
                "name": "Telugu",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "తెలుగు"
            },
            "tg": {
                "name": "Tajik",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "тоҷикӣ, toğikī, تاجیکی‎"
            },
            "th": {
                "name": "Thai",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ไทย"
            },
            "ti": {
                "name": "Tigrinya",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ትግርኛ"
            },
            "bo": {
                "name": "Tibetan Standard, Tibetan, Central",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "བོད་ཡིག"
            },
            "tk": {
                "name": "Turkmen",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Türkmen, Түркмен"
            },
            "tl": {
                "name": "Tagalog",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Wikang Tagalog"
            },
            "tn": {
                "name": "Tswana",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Setswana"
            },
            "to": {
                "name": "Tonga (Tonga Islands)",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "faka Tonga"
            },
            "tr": {
                "name": "Turkish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Türkçe"
            },
            "ts": {
                "name": "Tsonga",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Xitsonga"
            },
            "tt": {
                "name": "Tatar",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "татарча, tatarça, تاتارچا‎"
            },
            "tw": {
                "name": "Twi",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Twi"
            },
            "ty": {
                "name": "Tahitian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Reo Tahiti"
            },
            "ug": {
                "name": "Uighur",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Uyƣurqə, ئۇيغۇرچە‎"
            },
            "uk": {
                "name": "Ukrainian",
                "names": {self.NAME_EN: "Ukrainian", self.NAME_RU: "Украинский"},
                "native": "українська"
            },
            "ur": {
                "name": "Urdu",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "اردو"
            },
            "uz": {
                "name": "Uzbek",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "zbek, Ўзбек, أۇزبېك‎"
            },
            "ve": {
                "name": "Venda",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Tshivenḓa"
            },
            "vi": {
                "name": "Vietnamese",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Tiếng Việt"
            },
            "vo": {
                "name": "Volapük",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Volapük"
            },
            "wa": {
                "name": "Walloon",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Walon"
            },
            "cy": {
                "name": "Welsh",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Cymraeg"
            },
            "wo": {
                "name": "Wolof",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Wollof"
            },
            "fy": {
                "name": "Western Frisian",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Frysk"
            },
            "xh": {
                "name": "Xhosa",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "isiXhosa"
            },
            "yi": {
                "name": "Yiddish",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "ייִדיש"
            },
            "yo": {
                "name": "Yoruba",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
                "native": "Yorùbá"
            },
            "za": {
                "name": "Zhuang, Chuang",
                "names": {self.NAME_EN: "", self.NAME_RU: ""},
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
