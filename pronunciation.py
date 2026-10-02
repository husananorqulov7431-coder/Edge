import re

EASY_RATE=1.20
NORMAL_RATE=1.10
TERM_RATE=1.08
COMPLEX_RATE=1.00

TERMS=set('xromosoma xromosomalar hujayra membrana sitoplazma mitoxondriya ribosoma eritrotsit leykotsit gemoglobin trombotsit neyron sinaps akson dendrit gipofiz gipotalamus epiteliy ferment metabolizm xromatin genom dnk rnk atp aminokislota immunitet antigen antitelo mikroorganizm bakteriya virus farmakologiya patologiya fiziologiya anatomiya histologiya arteriya kapillyar miokard alveola bronx traxeya nefron mitoz meyoz replikatsiya transkripsiya translyatsiya plastida vakuola vakuala kutikula stroma xloroplast'.lower().split())
ABBR={'AI':'sun\'iy intellekt','TTS':'te te es','DTM':'de te em','PDF':'pe de ef','DOCX':'dok eks','TXT':'te eks te','DNK':'de en ka','RNK':'er en ka','ATP':'a te pe','ml':'millilitr','mg':'milligramm','kg':'kilogramm','km':'kilometr','mm':'millimetr','sm':'santimetr'}
APOSTROPHES='ʻʼ’‘`´ʹʺ＇'

def normalize_text(text):
    text=text.replace('\r\n','\n').replace('\r','\n')
    text=text.translate(str.maketrans({c:"'" for c in APOSTROPHES}))
    text=text.replace("o'",'o‘').replace("O'",'O‘').replace("g'",'g‘').replace("G'",'G‘')
    text=re.sub(r'[ \t]+',' ',text)
    return re.sub(r'\n{3,}','\n\n',text).strip()

def choose_rate(text):
    t=normalize_text(text).lower()
    words=re.findall(r"[a-zʻ‘’'-]+",t)
    terms=sum(w.strip("'‘’") in TERMS for w in words)
    long_words=sum(len(w.strip("'‘’"))>=12 for w in words)
    hard=sum(any(x in w for x in ('xrom','xl','g‘','o‘','str','nt','rt','sh','ch')) for w in words)
    score=terms*3+long_words*1.2+hard*0.35
    if score>=14 or long_words>=7 or hard>=14: return COMPLEX_RATE,'murakkab'
    if terms>=1: return TERM_RATE,'termin'
    if score>=4 or long_words>=2: return NORMAL_RATE,'qolgan'
    return EASY_RATE,'oddiy'

def prepare_for_tts(text):
    text=normalize_text(text)
    for src,dst in sorted(ABBR.items(),key=lambda x:-len(x[0])):
        text=re.sub(rf'(?<![A-Za-z]){re.escape(src)}(?![A-Za-z])',dst,text)
    text=text.replace('№','raqam ')
    text=text.replace('°C',' daraja Selsiy')
    text=re.sub(r'(?<!\w)(\d+(?:[.,]\d+)?)\s*%',r'\1 foiz',text)
    text=re.sub(r'(?<!\w)x(?!\w)','iks',text)
    text=re.sub(r',\s*(?=[A-Za-zÀ-žʻ‘’])',',,, ',text)
    return re.sub(r'\s{2,}',' ',text).strip()
