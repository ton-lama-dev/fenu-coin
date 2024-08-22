import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import markups
from markups import USER_MARKUP, USER_MARKUP_EN

import datetime
import time

import database
import config
from config import CHANNEL, ADMINS, TOKEN


bot = telebot.TeleBot(token=TOKEN, skip_pending=True)


admin_states = {}
admin_states_data = {}
link_wallet = set()
referrers = dict()

STATE_WAITING_FOR_PUBLIC_LINK = "waiting_for_public_link"
STATE_WAITING_FOR_PRIVATE_LINK = "waiting_for_private_link"
STATE_WAITING_FOR_REWARD = "waiting_for_reward"
STATE_WAITING_FOR_PUBLIC_LINK_TO_DELETE = "waiting_for_public_link_to_delete"
STATE_WAITING_FOR_BROADCAST_MESSAGE = "waiting_for_broadcast_message"
STATE_WAITING_FOR_BROADCAST_IMAGE = "waiting_for_broadcast_image"
STATE_WAITING_FOR_BROADCAST_BUTTON_NAME = "waiting_for_broadcast_name"
STATE_WAITING_FOR_BROADCAST_BUTTON_LINK = "waiting_for_broadcast_link"
STATE_WAITING_FOR_USER_ID_TO_GET_INFO = "waiting_for_user_id_to_get_info"
STATE_WAITING_FOR_USER_ID_TO_INCREASE_BALANCE = "waiting_for_user_id_to_increase_balance"
STATE_WAITING_FOR_NUMBER_TO_INCREASE_BALANCE = "waiting_for_number_to_increase_balance"


def is_subscribed_default(user_id):
    member = bot.get_chat_member(CHANNEL, user_id)
    return member.status in ["member", "administrator", "creator"]


def ask_to_subscribe(user_id):
    inline_markup = types.InlineKeyboardMarkup()
    language = database.get_language(user_id=user_id)
    URL = f"https://t.me/{CHANNEL[1:]}"
    inline_subscribe_button = types.InlineKeyboardButton(text="Подписаться", url=URL)
    inline_check_button = types.InlineKeyboardButton(text="Проверить" if language == "ru" else "Check", callback_data="callback_check_default_subscription")
    inline_markup.add(inline_subscribe_button, inline_check_button)
    bot.send_message(user_id, f"Пожалуйста, подпишитесь на канал {config.CHANNEL} чтобы продолжить использование бота." if language == "ru" else f"Please, subscribe to the channel {config.CHANNEL} to continue", reply_markup=inline_markup)


def ask_to_choose_language(user_id):
    text = "Выберите язык:\nChoose language:"
    inline_markup = InlineKeyboardMarkup(row_width=2)
    en_button = InlineKeyboardButton("🇺🇸", callback_data="set_en")
    ru_button = InlineKeyboardButton("🇷🇺", callback_data="set_ru")
    inline_markup.add(en_button, ru_button)
    bot.send_message(chat_id=user_id, text=text, reply_markup=inline_markup)


def send_message_by_language(user_id, ru_message, en_message, image=None):
    language = database.get_language(user_id=user_id)
    if image == None:
        if language == 'ru':
            bot.send_message(user_id, ru_message, reply_markup=USER_MARKUP)
        else:
            bot.send_message(user_id, en_message, reply_markup=USER_MARKUP_EN)
    else:
        photo = open(image, "rb")
        if language == 'ru':
            bot.send_photo(user_id, photo, ru_message, reply_markup=USER_MARKUP)
        else:
            bot.send_photo(user_id, photo, en_message, reply_markup=USER_MARKUP_EN)


def get_channel_id(channel_link):
    try:
        chat = bot.get_chat(channel_link)
        return chat.id
    except Exception as e:
        print(f"Не удалось получить ID канала")
        return None
    

def user_is_admin(user_id):
    return user_id in ADMINS


def public_link_is_valid(link):
    return get_channel_id(link) is not None


def user_is_subscribed_to_channel(user_id, public_link):
    try:
        member = bot.get_chat_member(public_link, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        pass


def add_channel(user_id):
    public_link = admin_states_data[user_id]["public_link"]
    private_link = admin_states_data[user_id]["private_link"]
    reward = admin_states_data[user_id]["reward"]
    database.add_channel_into_db(public_link=public_link, private_link=private_link, reward=reward)


def send_reward_to_referrer(referrer_id):
    database.send_reward_to_referrer(referrer_id=referrer_id)
    text = f"Кто-то присоединился к боту по вашей ссылке. Вам начислено {config.REFERRAL_REWARD} {config.COIN_NAME}!"
    bot.send_message(chat_id=referrer_id, text=text)


@bot.callback_query_handler(func=lambda call: call.data in ["set_ru", "set_en"])
def callback_set_language(call: types.CallbackQuery):
    user_id = call.from_user.id
    language = call.data[-2:]
    referrer = None
    if not database.is_user_in_db(user_id=user_id):
        if user_id in referrers:
            referrer_candidate = referrers[user_id]
            if database.is_user_in_db(user_id=referrer_candidate):
                if not referrer_candidate == user_id:
                    referrer = referrer_candidate
                    send_reward_to_referrer(referrer_id=referrer)
                    database.increase_referrals(user_id=referrer)
        if referrer != None:
            database.add_user_into_db(user_id=user_id, language=language, referrer=referrer)
        else:
            database.add_user_into_db(user_id=user_id, language=language)
        ru_text = f"Вам начислен приветственный бонус в размере {config.WELCOME_BONUS} {config.COIN_NAME}"
        en_text = f"You got a welcome bonus of {config.WELCOME_BONUS} {config.COIN_NAME}"
        send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)
    else:
        database.users_set(user_id=user_id, item="language", value=language)
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return


@bot.callback_query_handler(func=lambda call: call.data == "callback_check_default_subscription")
def callback_check_default_subscription(call):
    user_id = call.from_user.id
    language = database.get_language(user_id=user_id)
    user_is_subscribed = is_subscribed_default(user_id=user_id)
    if user_is_subscribed:
        image = open(f'images/img.jpg', 'rb')
        caption = f"Добро пожаловать в Neuro Mining!\n\n🚀 AirDrop будущего WebApp приложения с реальным доходом! \n\nВыполняйте задания, приглашайте друзей и получайте токен {config.COIN_NAME} а так же другие криптовалюты! Действуйте! \n\nНе упускайте возможность увеличить свой доход, действуйте⚡️" if language == "ru" else "Welcome to Neuro Mining!\n\n🚀 AirDrop of the future WebApp application with real income!\n\nComplete tasks, invite friends and get {config.COIN_NAME} token as well as other cryptocurrencies! Act!\n\nDon't miss the opportunity to increase your income, act⚡️"
        bot.send_photo(chat_id=user_id, photo=image, caption=caption, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN)
    else:
        ask_to_subscribe(user_id=user_id)


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    user_id = message.from_user.id
    referrer_id = None
    if " " in message.text:
        referrer_id = message.text.split()[1]
        referrers[user_id] = referrer_id
    else:
        referrers[user_id] = None
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    language = database.get_language(user_id=user_id)
    if not database.is_user_in_db(user_id=user_id):
        language = ask_to_choose_language(user_id=user_id)
    else:
        image = f"images/img.jpg"
        ru_caption = f"Добро пожаловать в Neuro Mining! \n\n🚀 AirDrop будущего WebApp приложения с реальным доходом! \n\nВыполняйте задания, приглашайте друзей и получайте токен {config.COIN_NAME} а так же другие криптовалюты!\n\nДействуйте! \n\nНе пропустите возможность увеличить свой доход, действуйте"
        en_caption = f"Welcome to Neuro Mining! \n\n🚀 AirDrop the future WebApp application with real income! \n\nComplete tasks, invite friends and receive a {config.COIN_NAME} token as well as other cryptocurrencies!\n\nTake action! \n\nDon't miss the opportunity to increase your income, take action"
        send_message_by_language(user_id=user_id, ru_message=ru_caption, en_message=en_caption, image=image)


@bot.message_handler(func=lambda message: message.text in markups.tasks_commands)
def cmd_tasks(message: types.Message):
    user_id = message.from_user.id
    language = database.get_language(user_id=user_id)
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    
    tasks = database.get_available_tasks(user_id=user_id)
    inline_markup = InlineKeyboardMarkup()
    #  suppose to get link without "@"
    for public_link in tasks:
        channel_name = bot.get_chat("@" + public_link).title
        reward = database.get_reward(public_link="@" + public_link)
        button = InlineKeyboardButton(f"{channel_name} | {reward} {config.COIN_NAME}", callback_data=f"channel_{public_link}")
        inline_markup.add(button)

    image = open(f"images/img.jpg", "rb")
    ru_text = f"За выполнение каждого задания вы получаете наш токен {config.COIN_NAME}\n\nЧем больше заданий вы выполните, тем больше токенов будет на вашем балансе!"
    en_text = f"For completing each task, you receive our {config.COIN_NAME} token.\n\nThe more tasks you complete, the more tokens you will have on your balance!"
    bot.send_photo(chat_id=user_id, photo=image, caption=ru_text if language == "ru" else en_text, reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("channel_"))
def channel_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    language = database.get_language(user_id=user_id)
    public_link = "@" + "_".join(call.data.split("_")[1:])
    private_link = database.get_channel_private_link(public_link=public_link)
    text = f"Подпишитесь на {public_link} и нажмите 'Проверить'" if language == 'ru' else f"Subscribe to {public_link} and press 'Check'"
    inline_markup = InlineKeyboardMarkup()
    check_button = InlineKeyboardButton(text="Проверить" if language == 'ru' else "Check", callback_data=f"check_{public_link}")
    subscribe_button = InlineKeyboardButton(text="Подписаться" if language == 'ru' else "Subscribe", url=private_link)
    inline_markup.add(subscribe_button, check_button)
    bot.send_message(chat_id=call.from_user.id, text=text, reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    public_link = "_".join(call.data.split("_")[1:])
    reward = database.get_reward(public_link=public_link)
    if not database.was_rewarded_for_subscription(user_id=user_id, public_link=public_link):
        if user_is_subscribed_to_channel(user_id=user_id, public_link=public_link):
            database.subscribe_user_to_channel(user_id=user_id, public_link=public_link)
            database.increase_task_done_times(public_link=public_link)
            database.reward_user_for_subscription(user_id=user_id, reward=reward)
            ru_text = f"Вам начислено {reward} {config.COIN_NAME}!"
            en_text = f"You got {reward} {config.COIN_NAME}!"
            send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)
        else:
            ru_text = f"Вы не подписались на канал."
            en_text = f"You didn't subscribed to the channel."
            send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)
    else:
        ru_text = f"Вы уже получили награду."
        en_text = f"You already got the reward."
        send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)


@bot.message_handler(func=lambda message: message.text in markups.balance_commands)
def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    language = database.get_language(user_id=user_id)
    image = open(f"images/img.jpg", "rb")
    balance = database.get_balance(user_id=user_id)
    referrals = database.get_referrals(user_id=user_id)
    referral_link = "https://t.me/Fehucoin_bot?start=" + str(user_id)
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Пригласить друзей' if language == 'ru' else "Invite friends", switch_inline_query=referral_link)
    markup.add(button)
    caption = f"Ваш баланс: {balance} {config.COIN_NAME}\n\nКоличество рефералов: {referrals}\n\nНаграда за 1 реферала: {config.REFERRAL_REWARD} {config.COIN_NAME}\n\nВаша реферальная ссылка: {referral_link}" if language == 'ru' else f"Your balance: {balance} {config.COIN_NAME}\n\nReferrals: {referrals}\n\nReward for 1 referral: {config.REFERRAL_REWARD} {config.COIN_NAME}\n\nYour referral link: {referral_link}"
    bot.send_photo(chat_id=user_id, photo=image, caption=caption, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in markups.claim_commands)
def cmd_get(message: types.Message):
    user_id = message.from_user.id
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return

    last_claim_time = database.get_last_claim(user_id=user_id)
    current_time = datetime.datetime.now()
    time_difference = current_time - last_claim_time

    if time_difference.total_seconds() >= config.CLAIM_INTERVAL * 3600:
        database.claim_reward(user_id=user_id)
        ru_text = f"Вам начислено {config.CLAIM_REWARD} {config.COIN_NAME}!\n\nСкоро выйдет наша игра и они тебе будут нужны, заходи каждый день 👋"
        en_text = f"You got {config.CLAIM_REWARD} {config.COIN_NAME}\n\nOur game will be released soon and you'll need them, log in every day👋"
        send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)
    else:
        remaining_time = datetime.timedelta(seconds=12 * 3600) - time_difference
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        ru_text = f"Вы уже получили токены, возвращайтесь через {hours} часов и {minutes} минут."
        en_text = f"You already got tokens, come back in {hours} hours an {minutes} minutes."
        send_message_by_language(user_id=user_id, ru_message=ru_text, en_message=en_text)


@bot.message_handler(func=lambda message: message.text in markups.wallet_commands)
def cmd_wallet(message: types.Message):
    user_id = message.from_user.id
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    language = database.get_language(user_id=user_id)
    wallet = database.get_wallet(user_id=user_id)
    text = f"Ваш кошелек: {wallet}\n\nВам нужно привязать некастодиальный кошелек сети TON - рекомендуем Tonkeeper/Tonhub/MyTonWallet" if language == "ru" else f"Your wallet: {wallet}\n\nYou have to connect a non-custodial wallet of TON - we recommend Tonkeeper/Tonhub/MyTonWallet"
    image = open(f"images/img.jpg", "rb")
    markup = types.InlineKeyboardMarkup()
    add_wallet_button = types.InlineKeyboardButton('Привязать кошелек' if language == "ru" 
                                                   else "Connect wallet", callback_data='add_wallet')
    markup.add(add_wallet_button)
    bot.send_photo(chat_id=user_id, photo=image, caption=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "add_wallet")
def callback_add_wallet(call):
    user_id = call.from_user.id
    language = database.get_language(user_id=user_id)
    answer = "Пожалуйста, пришлите адрес кошелька:\n\nИспользуйте только некастодиальные кошельки, такие как:\nTonSpace, MyTonWallet, Tonkeeper" if language == "ru" else "Please send the wallet address:\n\n Use only non-custodial wallets such as:\nTonSpace, MyTonWallet, Tonkeeper"
    bot.send_message(call.message.chat.id, text=answer, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN)
    link_wallet.add(user_id)


@bot.message_handler(func=lambda message: message.text in markups.info_commands)
def cmd_info(message: types.Message):
    user_id = message.from_user.id
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    language = database.get_language(user_id=user_id)
    text = f"Проект FEHU-COIN ставит перед собою амбициозную задачу создать инструмент получения прибыли для всех участников нашего сообщества из высокоприбыльных и технологичных источников .Вы получите наш токен $FEHU который даст много иксов на листинге! Но ещё до листинга сможете получать серьезную прибыль в ходе кампании распространения нашего токена . В том числе и в виде денежных средств на свои кошельки .\n\nСейчас основная задача — собрать или приобрести как можно больше наших токенов, это даст тебе возможность получать реальную прибыль!\n\n0.5 токенов $FEHU - За каждого приведенного друга! Чем больше у тебя друзей, тем больше $FEHU ты получишь\n0.5 токенов $FEHU -- за вход в бот ." if language == "ru" else f"The FEHU-COIN project has an ambitious goal of creating a tool for making a profit for all members of our community from highly profitable and technological sources. You will receive our $FEHU token, which will give you a lot of x's on the listing! But even before the listing, you will be able to make a serious profit during the distribution campaign of our token. Including in the form of cash to your wallets. \n\nNow the main task is to collect or purchase as many of our tokens as possible, this will give you the opportunity to make a real profit! \n\n0.5 $FEHU tokens - For each friend you bring! The more friends you have, the more $FEHU you will receive \n0.5 $FEHU tokens -- for entering the bot."
    image = open(f"images/img.jpg", "rb")
    bot.send_photo(chat_id=user_id, photo=image, caption=text, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN)


@bot.message_handler(func=lambda message: message.text in markups.buy_commands)
def cmd_info(message: types.Message):
    user_id = message.from_user.id
    if not database.is_user_in_db(user_id=user_id):
        ask_to_choose_language(user_id=user_id)
        return
    if not is_subscribed_default(user_id=user_id):
        ask_to_subscribe(user_id=user_id)
        return
    language = database.get_language(user_id=user_id)
    text = f"📈 Ранние пользователи могут приобрести {config.COIN_NAME} по цене пре-сейла!\n\nЦена одного токена - 1 USD. Чтобы поучаствовать в пре-сейле, отправте средства на один из адресов:\n\nСеть: BSC(BEP20) - USDT\nАдрес: 0x8B1AAEFb70Ecc077E85Fdecf8d1981BE39F84224\n\nСеть: TON - TON\nАдрес: UQARQ2tvxW_L1KkzxZEUsblU1PIRK5mzgCX4zmZ6ahvspA2X\n\nPayeer\nАдрес: P75034256\n\nПеревод на карту\nОбращаться к админу: @Bugirt\n\n✅На ваш кошелек поступят токены пропорционально количеству отправленных монет. Выплаты производятся 1 раз в сутки." if language == "ru" else f"📈 Early adopters can purchase {config.COIN_NAME} at the pre-sale price.\n\nThe price of one token is 1 USD. To participate in the pre-sale, send funds to one of the addresses:\n\nNetwork: BSC(BEP20) - USDT\nAddress: 0x8B1AAEFb70Ecc077E85Fdecf8d1981BE39F84224\n\nNetwork: TON - TON\nAddress: UQARQ2tvxW_L1KkzxZEUsblU1PIRK5mzgCX4zmZ6ahvspA2X\n\nPayeer\nAddress: P75034256\n\nCard transfer\nContact admin: @Bugirt\n\n✅Tokens will be credited to your wallet in proportion to the number of coins sent. Payments are made once a day."
    image = open(f"images/img.jpg", "rb")
    bot.send_photo(chat_id=user_id, photo=image, caption=text, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN)


@bot.message_handler(commands=["admin"])
def cmd_admin_panel(message: types.Message):
    user_id = message.from_user.id
    if not user_is_admin(user_id=user_id):
        return
    inline_markup = InlineKeyboardMarkup(row_width=1)
    users_button = InlineKeyboardButton("Пользователи 👨‍👩‍👧‍👦", callback_data="admin_users")
    statistics_button = InlineKeyboardButton("Статистика 📊", callback_data="admin_statistics")
    tasks_button = InlineKeyboardButton("Задания 📋", callback_data="admin_tasks")
    broadcast_button = InlineKeyboardButton("Рассылка 📩", callback_data="admin_broadcast")
    inline_markup.add(users_button, statistics_button, tasks_button, broadcast_button)
    bot.send_message(chat_id=user_id, text="Панель администратора", reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def callback_admin_broadcast(call):
    user_id = call.from_user.id
    admin_states[user_id] = STATE_WAITING_FOR_BROADCAST_MESSAGE
    text = "Отправьте сообщение для рассылки:"
    bot.send_message(chat_id=user_id, text=text)


@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def callback_admin_broadcast(call):
    user_id = call.from_user.id
    text = "/increase_balance - увеличить баланс пользователю\n/get_info - получить информацию о пользователе"
    bot.send_message(chat_id=user_id, text=text)


@bot.message_handler(commands=["increase_balance"])
def cmd_increase_balance(message: types.Message):
    user_id = message.from_user.id
    admin_states[user_id] = STATE_WAITING_FOR_USER_ID_TO_INCREASE_BALANCE
    text = "Отправьте ID пользователя:"
    bot.send_message(chat_id=user_id, text=text)


@bot.message_handler(commands=["get_info"])
def cmd_get_info(message: types.Message):
    user_id = message.from_user.id
    admin_states[user_id] = STATE_WAITING_FOR_USER_ID_TO_GET_INFO
    text = "Отправьте ID пользователя, информацию и котором вы хотите получить:"
    bot.send_message(chat_id=user_id, text=text)


@bot.callback_query_handler(func=lambda call: call.data == "admin_statistics")
def callback_admin_broadcast(call):
    user_id = call.from_user.id
    users = database.get_number_of_users()
    today = 0
    week = 0
    month = 0
    reg_dates = database.get_all_registration_dates()
    current_time = datetime.datetime.now()
    for reg_date in reg_dates:
        time_difference = current_time - reg_date
        if time_difference.total_seconds() <= 24 * 3600:
            today += 1
        elif time_difference.total_seconds() <= 168 * 3600:
            week += 1
        elif time_difference.total_seconds() <= 720 * 3600:
            month += 1
        else:
            break
    tasks_done = sum(database.get_all_tasks_done())
    balance = sum(database.get_all_balances())
    text = f"Статистика 📊\n\nКоличество пользователей: {users}\nСегодня: {today}\nЗа неделю: {week}\nЗа месяц: {month}\n\nВыполнено задач: {tasks_done}\n\nОбщий баланс: {balance}"
    bot.send_message(chat_id=user_id, text=text)


@bot.callback_query_handler(func=lambda call: call.data == "admin_tasks")
def callback_admin_tasks(call):
    user_id = call.from_user.id
    tasks = database.get_all_tasks()
    text = """/add - добавить задание\n/remove - удалить задание\n\nСтатистика по заданиям:"""
    for public_link in tasks:
        times_done = database.get_times_done(public_link=public_link)
        text += f"\n{public_link}: {times_done}"
    bot.send_message(chat_id=user_id, text=text)


def broadcast_message(admin_id):
    user_ids = database.get_all_users()
    language = database.get_language(user_id=admin_id)
    text = admin_states_data[admin_id]["broadcast_text"]
    image = admin_states_data[admin_id]["broadcast_image_id"]
    button_name = admin_states_data[admin_id]["broadcast_button_name"]
    button_link = admin_states_data[admin_id]["broadcast_button_link"]
    inline_markup = InlineKeyboardMarkup()
    inline_button = InlineKeyboardButton(text=button_name, url=button_link)
    inline_markup.add(inline_button)
    sent = 0
    not_sent = 0
    for user_id in user_ids:
        try:
            bot.send_photo(chat_id=user_id, photo=image, caption=text, reply_markup=inline_markup)
            sent += 1
        except Exception as e:
            print(e)
            not_sent += 1
    text = f"Рассылка завершена.\nОтправлено сообщений: {sent}\nНе удалось отправить: {not_sent}"
    bot.send_message(chat_id=admin_id, text=text, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN, parse_mode="HTML")


@bot.message_handler(commands=["add"])
def cmd_add(message: types.Message):
    user_id = message.from_user.id
    if not user_is_admin(user_id=user_id):
        return
    text = "Пришлите публичную ссылку канала вида @example:"
    bot.send_message(chat_id=user_id, text=text)
    admin_states[user_id] = STATE_WAITING_FOR_PUBLIC_LINK


@bot.message_handler(commands=["remove"])
def cmd_delete(message: types.Message):
    user_id = message.from_user.id
    if not user_is_admin(user_id=user_id):
        return
    text = "Пришлите публичную ссылку канала, который вы хотите удалить, вида @example:"
    bot.send_message(chat_id=user_id, text=text)
    admin_states[user_id] = STATE_WAITING_FOR_PUBLIC_LINK_TO_DELETE


@bot.message_handler(func=lambda message: True, content_types=["text", "photo"])
def handle_admin_message(message: types.Message):
    user_id = message.from_user.id
    language = database.get_language(user_id=user_id)
    global admin_states, admin_states_data, link_wallet

    if user_id in admin_states:
        if admin_states[user_id] == STATE_WAITING_FOR_PUBLIC_LINK:
            public_link = message.text
            if not public_link_is_valid(public_link):
                text = "Данная публичная ссылка не существует, попробуйте снова:"
                bot.send_message(chat_id=user_id, text=text)
                return
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["public_link"] = public_link
            text = "Отправьте специальную ссылку на канал (если ее нет - пришлите 0):"
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = STATE_WAITING_FOR_PRIVATE_LINK
            return

        if admin_states[user_id] == STATE_WAITING_FOR_PRIVATE_LINK:
            private_link = message.text
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            if message.text == "0":
                private_link = "https://t.me/" + admin_states_data[user_id]["public_link"][1:]
                admin_states_data[user_id]["private_link"] = private_link
            else:
                admin_states_data[user_id]["private_link"] = private_link
            admin_states[user_id] = STATE_WAITING_FOR_REWARD
            text = f"Установите размер вознаграждения за выполнение задания (цифра) :"
            bot.send_message(chat_id=user_id, text=text)
            return
        
        if admin_states[user_id] == STATE_WAITING_FOR_REWARD:
            string = message.text
            #  default reward
            reward = 100
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            try:
                reward = int(string)
            except:
                bot.send_message(chat_id=user_id, text="Это не число")
                return
            admin_states_data[user_id]["reward"] = reward
            add_channel(user_id)
            text = f"Канал успешно добавлен в задания."
            bot.send_message(chat_id=user_id, text=text)
            return

        if admin_states[user_id] == STATE_WAITING_FOR_PUBLIC_LINK_TO_DELETE:
            public_link = message.text
            if not database.is_channel_in_db(public_link):
                text = "Такого канала нет в заданиях, попробуйте снова:"
                bot.send_message(user_id, text=text)
            else:
                database.remove_channel_from_db(public_link=public_link)
                text = "Канал успешно удален из заданий."
                bot.send_message(chat_id=user_id, text=text)
                admin_states[user_id] = None  # Reset the state
            
        if admin_states[user_id] == STATE_WAITING_FOR_BROADCAST_MESSAGE:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["broadcast_text"] = message.text
            text = "Пришлите картинку для рассылки:"
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = STATE_WAITING_FOR_BROADCAST_IMAGE
            return

        if admin_states[user_id] == STATE_WAITING_FOR_BROADCAST_IMAGE and message.content_type == 'photo':
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["broadcast_image_id"] = message.photo[-1].file_id
            text = "Пришлите название кнопки для рассылки:"
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = STATE_WAITING_FOR_BROADCAST_BUTTON_NAME
            return

        if admin_states[user_id] == STATE_WAITING_FOR_BROADCAST_BUTTON_NAME:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["broadcast_button_name"] = message.text
            text = "Пришлите ссылку для кнопки:"
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = STATE_WAITING_FOR_BROADCAST_BUTTON_LINK
            return

        if admin_states[user_id] == STATE_WAITING_FOR_BROADCAST_BUTTON_LINK:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["broadcast_button_link"] = message.text
            text = "Рассылка успешно запущена. Вы получите сообщение по окончанию рассылки."
            bot.send_message(chat_id=user_id, text=text)
            broadcast_message(admin_id=user_id)
            admin_states[user_id] = None  # Reset the state

        if admin_states[user_id] == STATE_WAITING_FOR_USER_ID_TO_INCREASE_BALANCE:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["user_id"] = message.text
            text = "Отправьте число, на которое хотите увеличить баланс пользователя:"
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = STATE_WAITING_FOR_NUMBER_TO_INCREASE_BALANCE
            return

        if admin_states[user_id] == STATE_WAITING_FOR_NUMBER_TO_INCREASE_BALANCE:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            admin_states_data[user_id]["number"] = message.text
            text = "Баланс пользователя увеличен."
            bot.send_message(chat_id=user_id, text=text)
            admin_states[user_id] = None
            database.increase_user_balance(user_id=admin_states_data[user_id]["user_id"], number=admin_states_data[user_id]["number"])

        if admin_states[user_id] == STATE_WAITING_FOR_USER_ID_TO_GET_INFO:
            if user_id not in admin_states_data:
                admin_states_data[user_id] = {}
            id = message.text
            if database.is_user_in_db(user_id=id):
                data = database.get_user_info(user_id=user_id)
                user_id, balance, referrals, referrer, wallet, registration_date, language = data
                text = f"ID: {user_id}\nБаланс:{balance}\nКол-во рефералов: {referrals}\nРеферер: {referrer}\nКошелек: {wallet}\nПрисоединился: {registration_date}\nЯзык: {language}"
                bot.send_message(chat_id=user_id, text=text)
            else:
                bot.send_message(chat_id=user_id, text="Пользователя с таким ID не существует.")

            admin_states[user_id] = None

    if user_id in link_wallet:
        wallet = message.text
        database.update_wallet(user_id=user_id, wallet=wallet)
        text = 'Кошелек успешно привязан!'
        bot.send_message(chat_id=user_id, text=text, reply_markup=USER_MARKUP if language == "ru" else USER_MARKUP_EN)
        link_wallet.remove(user_id)  # Remove user from the link_wallet set after processing



if __name__ == "__main__":
    database.init_db()
    bot.polling(none_stop=True)