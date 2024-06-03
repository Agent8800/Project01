import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from subprocess import run

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Send me a video and subtitle file to burn subtitles into the video.')

def download_file(file_id, context):
    file = context.bot.get_file(file_id)
    file_path = os.path.join("downloads", file.file_id)
    file.download(file_path)
    return file_path

def handle_video(update: Update, context: CallbackContext) -> None:
    if update.message.video:
        video_file_id = update.message.video.file_id
        video_path = download_file(video_file_id, context)
        context.user_data['video_path'] = video_path
        update.message.reply_text('Video received. Now, send me the subtitle file.')

def handle_subtitle(update: Update, context: CallbackContext) -> None:
    if update.message.document:
        subtitle_file_id = update.message.document.file_id
        subtitle_path = download_file(subtitle_file_id, context)
        context.user_data['subtitle_path'] = subtitle_path
        update.message.reply_text('Subtitle received. Send the font style as plain text (e.g., Arial, 24, white).')

def handle_font(update: Update, context: CallbackContext) -> None:
    font_style = update.message.text
    context.user_data['font_style'] = font_style
    update.message.reply_text('Font style received. Now processing...')
    
    # Burn subtitles
    burn_subtitles(update, context)

def burn_subtitles(update: Update, context: CallbackContext) -> None:
    video_path = context.user_data.get('video_path')
    subtitle_path = context.user_data.get('subtitle_path')
    font_style = context.user_data.get('font_style')

    if video_path and subtitle_path and font_style:
        font_name, font_size, font_color = font_style.split(',')
        font_size = font_size.strip()
        font_color = font_color.strip()

        output_path = f'burned_{os.path.basename(video_path)}'
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles={subtitle_path}:force_style='FontName={font_name.strip()},FontSize={font_size},PrimaryColour=&H{font_color}&'",
            '-preset', 'fast',
            '-crf', '28',
            output_path
        ]
        run(command)

        with open(output_path, 'rb') as video_file:
            update.message.reply_video(video=video_file)

        # Cleanup
        os.remove(video_path)
        os.remove(subtitle_path)
        os.remove(output_path)
    else:
        update.message.reply_text('Error: Missing video, subtitle file, or font style.')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.video, handle_video))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_subtitle))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_font))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    main()
