import asyncio, os, re, tempfile
from pathlib import Path
import edge_tts
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message
from docx import Document

TOKEN = os.getenv("BOT_TOKEN")
VOICE = os.getenv("EDGE_VOICE", "uz-UZ-MadinaNeural")
DEFAULT_RATE = 1.2
MAX_CHARS = 14800
rates = {}

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
    await edge_tts.Communicate(text, VOICE, rate=edge_rate(rate)).save(str(out))

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
    rate = rates.get(message.from_user.id, DEFAULT_RATE)
    total = len(chunks)

    status = await message.answer(
        f"🎙 Tayyorlanmoqda…\n[░░░░░░░░░░] 0%\n"
        f"Qismlar: {total}\nTezlik: {rate:.1f}x"
    )

    with tempfile.TemporaryDirectory() as td:
        try:
            async def generate_part(index, chunk):
                out = Path(td) / f"part_{index:03d}.mp3"
                await make_audio(chunk, rate, out)
                return index, chunk, out

            # Barcha qismlar bir vaqtning o'zida yaratiladi.
            tasks = [
                asyncio.create_task(generate_part(index, chunk))
                for index, chunk in enumerate(chunks, 1)
            ]

            # Haqiqiy tugagan audio qismlar bo'yicha progress.
            completed = 0
            pending = set(tasks)
            while pending:
                done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                completed += len(done)
                await progress(
                    status,
                    completed,
                    total,
                    f"🎙 Parallel audio tayyorlanmoqda: {completed}/{total}",
                )

            # Natijalarni 1,2,3... tartibiga qaytaramiz.
            results = await asyncio.gather(*tasks)
            results.sort(key=lambda item: item[0])

            # Telegramga faqat tartibli yuboriladi.
            for index, chunk, out in results:
                await message.answer_audio(
                    FSInputFile(out),
                    caption=(
                        f"🎧 {index}-qism / {total}\n"
                        f"Belgilar: {len(chunk):,}\n"
                        f"Tezlik: {rate:.1f}x"
                    ),
                )

            await progress(status, total, total, "✅ Barcha qismlar tayyor")
            await status.edit_text(
                f"✅ Tayyor! {total} ta qism yuborildi.\n"
                f"Tezlik: {rate:.1f}x\n"
                f"Har qism: ko'pi bilan {MAX_CHARS:,} belgi."
            )
        except Exception as e:
            for task in locals().get("tasks", []):
                if not task.done():
                    task.cancel()
            await status.edit_text(f"❌ Ovoz yaratishda xatolik: {e}")

async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN secret topilmadi")

    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(m):
        rates[m.from_user.id] = DEFAULT_RATE
        await m.answer(
            "Assalomu alaykum!\n\n"
            "TXT, DOCX yoki oddiy matn yuboring. Men katta matnni "
            f"avtomatik {MAX_CHARS:,} belgigacha bo'lib, "
            "barcha qismlarni parallel audio qilaman va Telegramga "
            "1-qism, 2-qism tartibida yuboraman.\n\n"
            "/speed — joriy tezlik\n"
            "/speed 1.2 — tezlikni o'rnatish\n"
            "/speed 1.5 — masalan 1.5x\n\n"
            f"Standart tezlik: {DEFAULT_RATE:.1f}x"
        )

    @dp.message(Command("speed"))
    async def speed(m):
        args = (m.text or "").split(maxsplit=1)
        if len(args) == 1:
            await m.answer(
                f"Joriy tezlik: {rates.get(m.from_user.id, DEFAULT_RATE):.1f}x\n"
                "Oraliq: 0.5x–2.0x"
            )
            return
        try:
            rate = float(args[1].replace(",", "."))
            if not 0.5 <= rate <= 2.0:
                raise ValueError
        except ValueError:
            await m.answer(
                "Tezlik 0.5x–2.0x oralig'ida bo'lishi kerak. "
                "Masalan: /speed 1.4"
            )
            return
        rates[m.from_user.id] = rate
        await m.answer(f"✅ Tezlik saqlandi: {rate:.1f}x")

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
