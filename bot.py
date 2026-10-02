import asyncio, os, re, tempfile
from pathlib import Path
import edge_tts
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message
from docx import Document

TOKEN=os.getenv("BOT_TOKEN")
VOICE=os.getenv("EDGE_VOICE","uz-UZ-MadinaNeural")
DEFAULT_RATE=1.2
rates={}

def edge_rate(rate): return f"{round((rate-1)*100):+d}%"

def docx_text(p):
    d=Document(p)
    return "\n".join(x.text.strip() for x in d.paragraphs if x.text.strip())

async def make_audio(text, rate, out):
    await edge_tts.Communicate(text, VOICE, rate=edge_rate(rate)).save(str(out))

async def handle_text(message, text):
    text=re.sub(r"\r\n?","\n",text).strip()
    if not text:
        return await message.answer("Matn bo'sh.")
    if len(text)>15000:
        return await message.answer("Matn 15 000 belgidan oshmasin.")
    rate=rates.get(message.from_user.id,DEFAULT_RATE)
    msg=await message.answer(f"Tayyorlanmoqda… {rate:.1f}x")
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/"speech.mp3"
        try:
            await make_audio(text,rate,out)
            await message.answer_audio(FSInputFile(out),caption=f"Edge TTS • {rate:.1f}x")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Ovoz yaratishda xatolik: {e}")

async def main():
    if not TOKEN: raise RuntimeError("BOT_TOKEN secret topilmadi")
    dp=Dispatcher()

    @dp.message(CommandStart())
    async def start(m):
        rates[m.from_user.id]=DEFAULT_RATE
        await m.answer("Assalomu alaykum! TXT, DOCX yoki oddiy matn yuboring.\n\n/speed — tezlikni ko'rish\n/speed 1.2 — tezlikni o'rnatish\n\nStandart: 1.2x")

    @dp.message(Command("speed"))
    async def speed(m):
        a=(m.text or "").split(maxsplit=1)
        if len(a)==1:
            return await m.answer(f"Joriy tezlik: {rates.get(m.from_user.id,DEFAULT_RATE):.1f}x")
        try: rate=float(a[1].replace(",",".")); assert .5<=rate<=2
        except:
            return await m.answer("0.5x dan 2.0x gacha kiriting. Masalan: /speed 1.5")
        rates[m.from_user.id]=rate
        await m.answer(f"Tezlik: {rate:.1f}x")

    @dp.message(F.document)
    async def file(m,bot):
        name=m.document.file_name or "file"
        ext=Path(name).suffix.lower()
        if ext not in {".txt",".docx"}:
            return await m.answer("Faqat TXT va DOCX qabul qilinadi.")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/name
            await bot.download(m.document,destination=p)
            text=p.read_text(encoding="utf-8",errors="ignore") if ext==".txt" else docx_text(p)
            await handle_text(m,text)

    @dp.message(F.text)
    async def text(m):
        if not (m.text or "").startswith("/"): await handle_text(m,m.text or "")

    bot=Bot(TOKEN)
    await dp.start_polling(bot)

if __name__=="__main__": asyncio.run(main())
