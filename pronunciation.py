import re

# 0% = asl tezlik, musbat foiz = tezroq.
# Tibbiy/o'qishga mo'ljallangan matnda avtomatik ravishda nutqni sekinlashtiramiz.
EASY_RATE = 1.20
NORMAL_RATE = 1.10
TERM_RATE = 1.08
COMPLEX_RATE = 1.00

TERMS = set(
    """
    xromosoma xromosomalar hujayra membrana sitoplazma mitoxondriya
    ribosoma eritrotsit leykotsit gemoglobin trombotsit neyron sinaps
    akson dendrit gipofiz gipotalamus epiteliy ferment metabolizm xromatin
    genom dnk rnk atp aminokislota immunitet antigen antitelo mikroorganizm
    bakteriya virus farmakologiya patologiya fiziologiya anatomiya histologiya
    arteriya kapillyar miokard alveola bronx traxeya nefron mitoz meyoz
    replikatsiya transkripsiya translyatsiya plastida vakuola vakuala
    kutikula stroma xloroplast
    """.lower().split()
)

# Edge TTS ayrim tibbiy so'zlardagi qisqa "i" tovushini yutib yuborishi mumkin.
# Tirelar bo'g'inlarni aniqroq ajratib, talaffuzni barqarorlashtiradi.
TERM_PRONUNCIATION = {
    "sitoplazma": "si-toplazma",
    "mitoxondriya": "mi-to-xondriya",
    "ribosoma": "ri-bo-so-ma",
    "eritrotsit": "e-rit-ro-tsit",
    "leykotsit": "ley-ko-tsit",
    "trombotsit": "trom-bo-tsit",
    "miokard": "mi-o-kard",
    "sinaps": "si-naps",
    "immunitet": "im-mu-ni-tet",
    "mikroorganizm": "mi-kro-or-ga-nizm",
    "fiziologiya": "fi-zi-o-lo-gi-ya",
    "farmakologiya": "far-ma-ko-lo-gi-ya",
    "patologiya": "pa-to-lo-gi-ya",
    "anatomiya": "a-na-to-mi-ya",
    "histologiya": "his-to-lo-gi-ya",
    "gipofiz": "gi-po-fiz",
    "gipotalamus": "gi-po-ta-la-mus",
    "aminokislota": "a-mi-no-kis-lo-ta",
    "antigen": "an-ti-gen",
    "antitelo": "an-ti-te-lo",
    "replikatsiya": "rep-li-ka-tsi-ya",
    "transkripsiya": "tran-skrip-si-ya",
    "translyatsiya": "trans-lya-tsi-ya",
    "xromosoma": "xro-mo-so-ma",
    "xromosomalar": "xro-mo-so-ma-lar",
    "hujayra": "hu-jay-ra",
    "vakuola": "va-ku-o-la",
    "vakuala": "va-ku-a-la",
    "plastida": "plas-ti-da",
    "nefron": "nef-ron",
    "kutikula": "ku-ti-ku-la",
    "kutikulani": "ku-ti-ku-la-ni",
    "xloroplast": "xlo-ro-plast",
}

# Qisqartmalarni Edge TTS'ga harflab, aniq bo'g'inlar bilan beramiz.
ABBR = {
    "AI": "a-i",
    "TTS": "te-te-es",
    "DTM": "de-te-em",
    "PDF": "pe-de-ef",
    "DOCX": "dok-eks",
    # Edge TXT ni ba'zan "tex"ga yig'ib yuboradi.
    # Harf nomlarini aniqroq ajratish uchun "iks" shakli ishlatiladi.
    "TXT": "te-iks-te",
    "DNK": "de-en-ka",
    "RNK": "er-en-ka",
    "ATP": "a-te-pe",
    "ml": "millilitr",
    "mg": "milligramm",
    "kg": "kilogramm",
    "km": "kilometr",
    "mm": "millimetr",
    "sm": "santimetr",
}

# Uzbek matnlarida uchraydigan apostrof variantlarini bir xil standartga keltiramiz.
# U+02BB (ʻ) ishlatiladi: oʻ, gʻ.
APOSTROPHES = "'ʻʼ’‘\x60´ʹʺ＇"


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(str.maketrans({c: "ʻ" for c in APOSTROPHES}))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _replace_whole_words(text, mapping):
    for src, dst in sorted(mapping.items(), key=lambda x: -len(x[0])):
        pattern = rf"(?<![\wʻ]){re.escape(src)}(?![\wʻ])"
        text = re.sub(pattern, dst, text, flags=re.IGNORECASE)
    return text


def _sh_ch_ng_hits(text):
    # Faqat sh/ch/ng ga boy parchalarni aniqlaymiz.
    # Bunday ro'yxatlarda asosiy maqsad tezlik emas, aniq talaffuz.
    return len(
        re.findall(r"sh|ch|ng", normalize_text(text).lower())
    )


def _is_sh_ch_ng_sensitive(text):
    words = re.findall(r"[a-zʻ]+(?:['ʻ’-][a-zʻ]+)*", normalize_text(text).lower())
    hits = _sh_ch_ng_hits(text)
    return len(words) >= 4 and hits >= 5


def _strengthen_pauses(text, sensitive=False):
    # Edge TTS custom SSML/phoneme'ni qabul qilmaydi; shuning uchun
    # oddiy matn punktuatsiyasi orqali pauzani kuchaytiramiz.
    # Ro'yxat va ketma-ket tushunchalarda semicolon verguldan aniqroq pauza beradi.
    text = re.sub(r"(?<![0-9]),\s*(?=[A-Za-zʻ])", "; ", text)

    # Faqat sh/ch/ng ga boy ro'yxatda "va"ni ham alohida ajratamiz.
    # Boshqa matnlarning oqimini o'zgartirmaymiz.
    if sensitive:
        text = re.sub(r"\s+va\s+", "; va; ", text, flags=re.IGNORECASE)

    return text


def choose_rate(text):
    t = normalize_text(text).lower()
    words = re.findall(r"[a-zʻ]+(?:['ʻ’-][a-zʻ]+)*", t)
    if not words:
        return EASY_RATE, "oddiy"

    terms = sum(w.strip("ʻ’'") in TERMS for w in words)
    long_words = sum(len(w.strip("ʻ’'")) >= 12 for w in words)
    hard = sum(
        any(x in w for x in ("xrom", "xl", "gʻ", "oʻ", "str", "nt", "rt", "sh", "ch", "ng"))
        for w in words
    )
    term_density = terms / max(len(words), 1)

    # sh/ch/ng tovushlari ko'p bo'lgan maxsus mashq yoki ro'yxat:
    # aynan shu holatda 0% tezlikni tanlaymiz.
    if _is_sh_ch_ng_sensitive(t):
        return COMPLEX_RATE, "talaffuz"

    # Ko'p tibbiy termin birga kelsa, butun qismni sezilarli sekinlashtiramiz.
    if terms >= 5 or term_density >= 0.16 or long_words >= 9 or hard >= 18:
        return COMPLEX_RATE, "murakkab"
    if terms >= 1 or long_words >= 4 or hard >= 8:
        return TERM_RATE, "termin"
    if long_words >= 2 or hard >= 4:
        return NORMAL_RATE, "qolgan"
    return EASY_RATE, "oddiy"


def prepare_for_tts(text):
    text = normalize_text(text)
    sensitive = _is_sh_ch_ng_sensitive(text)

    # 1) Qisqartmalar.
    text = _replace_whole_words(text, ABBR)

    # 2) Belgilar va birliklar.
    text = text.replace("№", "raqam ")
    text = text.replace("°C", " daraja Selsiy")
    text = re.sub(r"(?<!\w)(\d+(?:[.,]\d+)?)\s*%", r"\1 foiz", text)

    # 3) Tibbiy terminlar: ayniqsa "i" tovushini himoya qilamiz.
    text = _replace_whole_words(text, TERM_PRONUNCIATION)

    # 4) Matematik x ni faqat mustaqil belgi bo'lsa "iks" qilamiz.
    # xromosoma, xloroplast kabi so'zlarning ichiga tegmaymiz.
    text = re.sub(r"(?<!\w)x(?!\w)", "iks", text, flags=re.IGNORECASE)

    # 5) Kuchliroq, tabiiyroq mikro-pauzalar.
    text = _strengthen_pauses(text, sensitive=sensitive)

    # 6) Bo'shliqlarni yakuniy tozalash.
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text
