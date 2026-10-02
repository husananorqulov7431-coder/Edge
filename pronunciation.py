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

WORD_RE = re.compile(r"[a-zʻ]+(?:['ʻ’-][a-zʻ]+)*", re.IGNORECASE)

# Yuqori ishonch bilan avtomatik fonetik moslash mumkin bo'lgan
# tibbiy/ilmiy ildizlar. Lug'atda bo'lmagan yangi terminlar shu qatlamdan
# aniqlanadi.
TECHNICAL_ROOTS = (
    "glomer",
    "nefro",
    "nefr",
    "gastro",
    "entero",
    "hepat",
    "reno",
    "kardio",
    "angio",
    "neuro",
    "osteo",
    "artro",
    "dermato",
    "derm",
    "oto",
    "oftal",
    "endo",
    "ekzo",
    "exo",
    "bronxo",
    "pnevmo",
    "pulmono",
    "laring",
    "faring",
    "rin",
    "traxe",
    "immuno",
    "immunoglob",
    "mikro",
    "makro",
    "sito",
    "cito",
    "gisto",
    "bio",
    "elektro",
    "kardi",
    "farmako",
    "patolog",
    "fiziolog",
    "anatomo",
    "histolog",
    "onkolog",
    "genom",
    "genetik",
    "embri",
    "embrio",
    "endokrin",
    "gormon",
    "metabol",
    "proteino",
    "peptid",
    "lipid",
    "glyuko",
    "gluko",
    "eritro",
    "leuko",
    "trombo",
    "gemato",
    "gemoglobin",
    "plazma",
    "oste",
    "morfolog",
    "mikroskop",
    "biops",
    "sitolog",
)

TECHNICAL_SUFFIXES = (
    "ologiya",
    "ologik",
    "skopiya",
    "skop",
    "grafiya",
    "grafik",
    "metriya",
    "metrik",
    "tomiya",
    "ektomiya",
    "plaziya",
    "plastika",
    "patologiya",
    "geneziya",
    "genez",
    "genetik",
    "megaliya",
    "peniya",
    "kineziya",
    "staziya",
    "farmakologiya",
    "fiziologiya",
    "histologiya",
    "anatomiya",
    "it",
    "oma",
    "emiya",
)

# Sözning oxiridagi o'zbek qo'shimchalari. Avval lug'atdagi termin ildizi
# taniladi, keyin qo'shimcha asl shaklda ulanadi.
TERM_SUFFIXES = (
    "larining",
    "laringiz",
    "laridan",
    "lariga",
    "larini",
    "larning",
    "lardagi",
    "lardan",
    "larga",
    "larni",
    "lari",
    "dagi",
    "dan",
    "ning",
    "ga",
    "ka",
    "da",
    "ta",
    "ni",
    "lar",
    "dan",
    "li",
    "lik",
    "siz",
    "cha",
)

# Juda qisqa yoki odatiy so'zlar uchun fonetik qayta yozish xavfli.
# Bu ro'yxat technical candidate filtrining qo'shimcha xavfsizlik qatlamidir.
SAFE_COMMON_WORDS = set(
    """
    shifokor bemor dori davolash kasallik odam inson organ tizim tibbiyot
    universitet talabalar talaba o'qituvchi kitob matn savol javob kerak
    qilish bo'lish uchun bilan haqida orqali hamda va yoki bu shu bir ikki
    uch yangi umumiy asosiy muhim normal yuqori past chap o'ng old orqa
    sabab natija jarayon usul qism qismiga mashq rasm jadval ma'lumot
    """.lower().split()
)

VOWELS = {"a", "e", "i", "o", "u", "oʻ"}
DIGRAPHS = ("sh", "ch", "ng")


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


def _term_pronunciation(word):
    """Exact termin yoki uning o'zbekcha qo'shimchali shakli."""
    lower = word.lower().strip("ʻ’'")
    exact = TERM_PRONUNCIATION.get(lower)
    if exact:
        return exact

    for suffix in sorted(TERM_SUFFIXES, key=len, reverse=True):
        if not lower.endswith(suffix):
            continue
        stem = lower[:-len(suffix)]
        base = TERM_PRONUNCIATION.get(stem)
        if base:
            return f"{base}-{suffix}"

    return None


def _tokenize_phonetic_units(word):
    """Bo'g'inlashda sh/ch/ng va o'/'g' kabi birliklarni buzmaydi."""
    word = word.lower()
    units = []
    i = 0

    while i < len(word):
        if word[i : i + 2] in DIGRAPHS:
            units.append(word[i : i + 2])
            i += 2
            continue
        if word[i : i + 2] == "oʻ":
            units.append("oʻ")
            i += 2
            continue
        if word[i : i + 2] == "gʻ":
            units.append("gʻ")
            i += 2
            continue
        units.append(word[i])
        i += 1

    return units


def _syllabify_unknown_word(word):
    """
    Yuqori ishonchli yangi terminlarni konservativ tarzda bo'g'inlaydi.
    Qoidasi:
      - 1 undosh ikki unli orasida -> undosh keyingi bo'g'inga;
      - 2+ undosh -> birinchi undosh oldingi bo'g'inda, qolganlari keyingisida.
    Bu Edge TTS'ga tabiiy mikro-pauza va artikulyatsiya beradi.
    """
    units = _tokenize_phonetic_units(word)
    vowel_indexes = [i for i, unit in enumerate(units) if unit in VOWELS]

    if len(vowel_indexes) < 2:
        return word

    boundaries = set()

    for left, right in zip(vowel_indexes, vowel_indexes[1:]):
        between = right - left - 1
        if between <= 0:
            # Ketma-ket unli: keyingi unli yangi bo'g'inni boshlaydi.
            boundaries.add(right)
        elif between == 1:
            boundaries.add(left + 1)
        else:
            # Masalan: nef-rit -> e-f-r-i oralig'ida bo'g'in chegarasi
            # f dan keyin bo'ladi.
            boundaries.add(left + 2)

    syllables = []
    start = 0
    for boundary in sorted(b for b in boundaries if 0 < b < len(units)):
        syllables.append("".join(units[start:boundary]))
        start = boundary
    syllables.append("".join(units[start:]))

    syllables = [s for s in syllables if s]
    return "-".join(syllables) if len(syllables) >= 2 else word


def _technical_candidate(word):
    """Lug'atda yo'q, ammo tibbiy/ilmiy termin bo'lish ehtimoli yuqori so'zni topadi."""
    lower = word.lower().strip("ʻ’'")

    if not lower or lower in SAFE_COMMON_WORDS:
        return False
    if len(lower) < 9:
        return False
    if not re.fullmatch(r"[a-zʻ]+", lower):
        return False

    root_hit = any(root in lower for root in TECHNICAL_ROOTS)
    suffix_hit = any(lower.endswith(suffix) for suffix in TECHNICAL_SUFFIXES)

    # Kamida bitta kuchli ilmiy belgi bo'lishi shart.
    if not (root_hit or suffix_hit):
        return False

    # Bir nechta undoshlar ketma-ketligi bo'lgan uzun terminlar qo'shimcha
    # ishonch beradi, lekin oddiy so'zlarni qayta yozishga majburlamaymiz.
    complex_pattern = any(
        pattern in lower
        for pattern in ("str", "skr", "tr", "dr", "kr", "gr", "pl", "bl", "kl", "fr", "x", "gʻ", "oʻ")
    )
    return complex_pattern or root_hit


def _auto_pronunciation(word):
    exact = _term_pronunciation(word)
    if exact:
        return exact, "exact"

    if _technical_candidate(word):
        syllables = _syllabify_unknown_word(word)
        if syllables != word:
            return syllables, "auto"

    return word, None


def _transform_candidate_words(text):
    def repl(match):
        word = match.group(0)

        # Oldindan tayyorlangan bo'g'inli qisqartmalarni qayta bo'lmaymiz.
        if "-" in word:
            return word

        transformed, _ = _auto_pronunciation(word)
        return transformed

    return WORD_RE.sub(repl, text)


def _sh_ch_ng_hits(text):
    # Faqat sh/ch/ng ga boy parchalarni aniqlaymiz.
    # Bunday ro'yxatlarda asosiy maqsad tezlik emas, aniq talaffuz.
    return len(re.findall(r"sh|ch|ng", normalize_text(text).lower()))


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
    auto_candidates = sum(_technical_candidate(w) for w in words)
    long_words = sum(len(w.strip("ʻ’'")) >= 12 for w in words)
    hard = sum(
        any(x in w for x in ("xrom", "xl", "gʻ", "oʻ", "str", "nt", "rt", "sh", "ch", "ng"))
        for w in words
    )
    term_density = (terms + auto_candidates) / max(len(words), 1)

    # sh/ch/ng tovushlari ko'p bo'lgan maxsus mashq yoki ro'yxat:
    # aynan shu holatda 0% tezlikni tanlaymiz.
    if _is_sh_ch_ng_sensitive(t):
        return COMPLEX_RATE, "talaffuz"

    # Yangi, lekin yuqori ehtimolli ilmiy termin bo'lsa, Edge TTS'ga
    # qo'shimcha artikulyatsiya va vaqt beramiz.
    if auto_candidates >= 3 or terms >= 5 or term_density >= 0.16 or long_words >= 9 or hard >= 18:
        return COMPLEX_RATE, "murakkab"
    if auto_candidates >= 1 or terms >= 1 or long_words >= 4 or hard >= 8:
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

    # 3) Exact terminlar + qo'shimchali shakllar + yangi ilmiy terminlar.
    text = _transform_candidate_words(text)

    # 4) Matematik x ni faqat mustaqil belgi bo'lsa "iks" qilamiz.
    # xromosoma, xloroplast kabi so'zlarning ichiga tegmaymiz.
    text = re.sub(r"(?<!\w)x(?!\w)", "iks", text, flags=re.IGNORECASE)

    # 5) Kuchliroq, tabiiyroq mikro-pauzalar.
    text = _strengthen_pauses(text, sensitive=sensitive)

    # 6) Bo'shliqlarni yakuniy tozalash.
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text
