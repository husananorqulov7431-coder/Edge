import asyncio, os, re, tempfile
from pathlib import Path
import edge_tts
from pronunciation import choose_rate, prepare_for_tts
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message
from docx import Document

TOKEN = os.getenv("BOT_TOKEN")
VOICE = os.getenv("EDGE_VOICE", "uz-UZ-MadinaNeural")
DEFAULT_RATE = 1.2
MAX_CHARS = 14800
rates = {}
auto_mode = {}

def edge_rate(rate):
    return f"{round((rate - 1) * 100):+d}%"

def docx_text(path):
    doc = Document(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_text(text, max_chars=MAX_CHARS):
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text]
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks, current = [], ""

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    def add_piece(piece):
        nonlocal current
        piece = piece.strip()
        if not piece:
            return
        candidate = piece if not current else current + "\n\n" + piece
        if len(candidate) <= max_chars:
            current = candidate
        else:
            flush()
            current = piece

    for block in blocks:
        if len(block) <= max_chars:
            add_piece(block)
            continue
        sentences = re.split(r"(?<=[.!?…])\s+", block)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) <= max_chars:
                add_piece(sentence)
                continue
            words, buf = sentence.split(), ""
            for word in words:
                candidate = word if not buf else buf + " " + word
                if len(candidate) <= max_chars:
                    buf = candidate
                else:
                    if buf:
                        add_piece(buf)
                    while len(word) > max_chars:
                        add_piece(word[:max_chars])
                        word = word[max_chars:]
                    buf = word
            if buf:
                add_piece(buf)
    flush()
    return chunks

async def make_audio(text, rate, out):
    prepared = prepare_for_tts(text)
    await edge_tts.Communicate(prepared, VOICE, rate=edge_rate(rate)).save(str(out))

async def progress(status, current, total, label):
    percent = round(current / total * 100)
    filled = percent // 10
    bar = "█" * filled + "░" * (10 - filled)
    await status.edit_text(
        f"🎙 {label}\n[{bar}] {percent}%\nQism: {current}/{total}"
    )

async def handle_text(message, text):
    text = normalize_text(text)
    if not text:
        await message.answer("Matn bo'sh.")
        return

    chunks = split_text(text)
    user_id = message.from_user.id
    auto = auto_mode.get(user_id, True)
    selected = []
    for chunk in chunks:
        if auto:
            part_rate, level = choose_rate(chunk)
        else:
            part_rate, level = rates.get(user_id, DEFAULT_RATE), "qo'lda"
        selected.append((part_rate, level, chunk))

    total = len(chunks)
    mode_label = "AUTO" if auto else "QO'LLANMA"
    status = await message.answer(
        f"Tayyorlanmoqda...\n[░░░░░░░░░░] 0%\n"
        f"Qismlar: {total}\nRejim: {mode_label}"
    )

    with tempfile.TemporaryDirectory() as td:
        tasks = []
        try:
            async def generate_part(index, chunk, part_rate, level):
                out = Path(td) / f"part_{index:03d}.mp3"
                await make_audio(chunk, part_rate, out)
                return index, chunk, out, part_rate, level

            tasks = [
                asyncio.create_task(generate_part(index, chunk, part_rate, level))
                for index, (part_rate, level, chunk) in enumerate(selected, 1)
            ]

            completed = 0
            pending = set(tasks)
            while pending:
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )
                completed += len(done)
                await progress(
                    status, completed, total,
                    f"Parallel audio tayyorlanmoqda: {completed}/{total}",
                )

            results = await asyncio.gather(*tasks)
            results.sort(key=lambda item: item[0])

            for index, chunk, out, part_rate, level in results:
                await message.answer_audio(
                    FSInputFile(out),
                    caption=(
                        f"{index}-qism / {total}\n"
                        f"Belgilar: {len(chunk):,}\n"
                        f"Daraja: {level}\n"
                        f"Tezlik: {part_rate:.2f}x | Rate: {edge_rate(part_rate)}"
                    ),
                )

            if auto:
                await status.edit_text(
                    f"Tayyor! {total} ta qism yuborildi.\n"
                    "AUTO: 1.00x (+0%) murakkab | 1.08x (+8%) termin | "
                    "1.10x (+10%) qolgan | 1.20x (+20%) oddiy"
                )
            else:
                await status.edit_text(
                    f"Tayyor! {total} ta qism yuborildi.\n"
                    f"QO'LLANMA: {rates.get(user_id, DEFAULT_RATE):.2f}x"
                )
        except Exception as e:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await status.edit_text(f"Ovoz yaratishda xatolik: {e}")
async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN secret topilmadi")

    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(m):
        rates[m.from_user.id] = DEFAULT_RATE
        auto_mode[m.from_user.id] = True
        await m.answer(
            "Assalomu alaykum!\n\n"
            "TXT, DOCX yoki oddiy matn yuboring. Men katta matnni "
            f"avtomatik {MAX_CHARS:,} belgigacha bo'lib, "
            "barcha qismlarni parallel audio qilaman va Telegramga "
            "1-qism, 2-qism tartibida yuboraman.\n\n"
            "/speed — joriy rejim\n"
            "/speed auto — aqlli avtomatik rejim\n"
            "/speed 1.2 — qo'lda tezlik\n\n"
            "AUTO: 1.00x murakkab, 1.08x termin, "
            "1.10x qolgan, 1.20x oddiy."
        )

    @dp.message(Command("speed"))
    async def speed(m):
        args = (m.text or "").split(maxsplit=1)
        if len(args) == 1:
            if auto_mode.get(m.from_user.id, True):
                await m.answer("AUTO: 1.00x (+0%) murakkab | 1.08x (+8%) termin | 1.10x (+10%) qolgan | 1.20x oddiy (+20%)")
            else:
                await m.answer(f"QO'LLANMA: {rates.get(m.from_user.id, DEFAULT_RATE):.2f}x")
            return
        arg = args[1].strip().lower()
        if arg == "auto":
            auto_mode[m.from_user.id] = True
            await m.answer("AUTO yoqildi: +0% / +8% / +10% / +20% (1.00x / 1.08x / 1.10x / 1.20x)")
            return
        try:
            rate = float(arg.replace(",", "."))
            if not 0.5 <= rate <= 2.0:
                raise ValueError
        except ValueError:
            await m.answer("/speed auto yoki 0.5x-2.0x oralig'idagi qiymat: /speed 1.4")
            return
        rates[m.from_user.id] = rate
        auto_mode[m.from_user.id] = False
        await m.answer(f"Qo'lda tezlik: {rate:.2f}x")
    @dp.message(F.document)
    async def file_handler(m, bot):
        name = m.document.file_name or "file"
        ext = Path(name).suffix.lower()
        if ext not in {".txt", ".docx"}:
            await m.answer("Faqat TXT va DOCX fayl qabul qilinadi.")
            return
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / name
            await bot.download(m.document, destination=path)
            if ext == ".txt":
                text = path.read_text(encoding="utf-8", errors="ignore")
            else:
                text = docx_text(path)
            await handle_text(m, text)

    @dp.message(F.text)
    async def text_handler(m):
        if not (m.text or "").startswith("/"):
            await handle_text(m, m.text or "")

    bot = Bot(TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
