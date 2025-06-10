import os
import logging
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from moviepy import VideoFileClip

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me a video (under 20 MB), and I will trim the first 15 seconds.')

async def trim_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trims the first 15 seconds of a received video."""
    try:
        video_file = await update.message.video.get_file()
        original_video_path = f'{video_file.file_id}.mp4'
        trimmed_video_path = f'trimmed_{video_file.file_id}.mp4'

        await update.message.reply_text('Downloading...')
        await video_file.download_to_drive(original_video_path)
        await update.message.reply_text('Video downloaded. Starting to trim...')

        # Load the video and trim it
        clip = VideoFileClip(original_video_path)
        if clip.duration > 15:
            trimmed_clip = clip.subclip(15)
            trimmed_clip.write_videofile(trimmed_video_path, logger=None) # Added logger=None to hide moviepy console spam
            await update.message.reply_text('Video trimmed successfully! Sending it back...')
            with open(trimmed_video_path, 'rb') as video:
                await update.message.reply_video(video=video)
        else:
            await update.message.reply_text('The video is less than 15 seconds long and cannot be trimmed.')

    except BadRequest as e:
        # This block catches Telegram's specific errors
        if "File is too large" in e.message:
            await update.message.reply_text('Sorry, this video is larger than 20 MB. I cannot process it due to Telegram limitations.')
        else:
            await update.message.reply_text(f'A Telegram error occurred: {e.message}')

    except Exception as e:
        # This block catches other errors (like a broken video file)
        logger.error(f"Error processing video: {e}")
        await update.message.reply_text('Sorry, there was an unexpected error processing your video.')

    finally:
        # Clean up the video files from the server
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(trimmed_video_path):
            os.remove(trimmed_video_path)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, trim_video))

    application.run_polling()

if __name__ == '__main__':
    main()
    
