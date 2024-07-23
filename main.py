from instagrapi import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import getpass

def login_instagram():
    username = input("Введите логин: ")
    password = getpass.getpass('Введите пароль: ')

    cl = Client()

    try:
        cl.login(username, password)
        print("Вход выполнен успешно")
    except instagrapi.exceptions.TwoFactorRequired as e:
        print("Требуется двухфакторная аутентификация")
        verification_code = input('Введите код двухфакторной аутентификации: ')
        try:
            cl.two_factor_login(username, password, verification_code)
            print("Вход выполнен успешно с двухфакторной аутентификацией")
        except Exception as e:
            print(f"Ошибка при входе: {e}")
            exit()
    
    return cl

# Авторизуемся в Instagram
cl = login_instagram()

# Функция для разбивки текста на части
def split_text(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! Use /getinfo <username> to choose what information you want to get.')

async def getinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        target_username = context.args[0]
        context.user_data['target_username'] = target_username
        keyboard = [
            [
                InlineKeyboardButton("Followers", callback_data='followers'),
                InlineKeyboardButton("Following", callback_data='following'),
            ],
            [
                InlineKeyboardButton("Posts", callback_data='posts'),
                InlineKeyboardButton("Reels", callback_data='reels'),
            ],
            [
                InlineKeyboardButton("Tagged Posts", callback_data='tagged_posts'),
                InlineKeyboardButton("Stories", callback_data='stories'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('What information do you want to get?', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Please provide a username using the command: /getinfo <username>')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    target_username = context.user_data.get('target_username')
    if not target_username:
        await query.edit_message_text(text="Please use /getinfo <username> to start.")
        return

    data = query.data
    try:
        # Получаем профиль пользователя
        user_id = cl.user_id_from_username(target_username)
        profile = cl.user_info(user_id)

        if data == 'followers':
            # Получаем и отправляем список подписчиков
            followers = cl.user_followers(user_id)
            response = '\n'.join(follower.username for follower in followers.values())
            await query.message.reply_text(response)

        elif data == 'following':
            # Получаем и отправляем список подписок
            following = cl.user_following(user_id)
            response = '\n'.join(followee.username for followee in following.values())
            await query.message.reply_text(response)

        elif data == 'posts':
            # Получаем и отправляем информацию о постах
            posts = cl.user_medias(user_id, 20)
            posts_info = [f'Post from {post.taken_at}:\nCaption: {post.caption_text}\nLikes: {post.like_count}, Comments: {post.comment_count}\nURL: {post.thumbnail_url}\n---\n' for post in posts]
            for part in split_text('\n'.join(posts_info)):
                await query.message.reply_text(part)

        elif data == 'reels':
            # Получаем и отправляем информацию о Reels
            reels = cl.user_medias(user_id, 20)
            reels_info = [f'Reel from {reel.taken_at}:\nCaption: {reel.caption_text}\nLikes: {reel.like_count}, Comments: {reel.comment_count}\nURL: {reel.video_url}\n---\n' for reel in reels if reel.media_type == 2]
            for part in split_text('\n'.join(reels_info)):
                await query.message.reply_text(part)

        elif data == 'tagged_posts':
            # Получаем и отправляем информацию об отмеченных постах
            tagged_posts = cl.usertag_medias(user_id, 20)
            tagged_posts_info = [f'Tagged Post from {post.taken_at}:\nCaption: {post.caption_text}\nLikes: {post.like_count}, Comments: {post.comment_count}\nURL: {post.thumbnail_url}\n---\n' for post in tagged_posts]
            for part in split_text('\n'.join(tagged_posts_info)):
                await query.message.reply_text(part)

        elif data == 'stories':
            # Получаем и отправляем информацию о историях
            stories = cl.user_stories(user_id)
            stories_info = [f'Story from {story.taken_at}:\nURL: {story.video_url if story.media_type == 2 else story.thumbnail_url}\n---\n' for story in stories]
            for part in split_text('\n'.join(stories_info)):
                await query.message.reply_text(part)

    except Exception as e:
        await query.edit_message_text(text=f'An error occurred: {e}')

# Создаем и запускаем Telegram-бота
app = ApplicationBuilder().token("6909200040:AAGo9GJxfXZXaNd4Z6Wb8jDdM8-ZmF5_1lE").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getinfo", getinfo))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
