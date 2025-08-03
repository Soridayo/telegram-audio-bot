import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, filters
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео, и я пришлю аудио с обложкой 🎵")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Скачиваю...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio')
            filename = f"{title}.mp3"
            thumbnail = f"{title}.webp"

        audio = MP3(filename, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=title))
        if os.path.exists(thumbnail):
            with open(thumbnail, 'rb') as img:
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/webp',
                    type=3,
                    desc='Cover',
                    data=img.read()
                ))
        audio.save()

        await update.message.reply_audio(audio=open(filename, "rb"), title=title)
        os.remove(filename)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)

    except Exception as e:
        await update.message.reply_text("Ошибка: " + str(e))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download))
app.run_polling()
