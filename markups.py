from telebot import types


USER_MARKUP = types.ReplyKeyboardMarkup(resize_keyboard=True)
balance_button = types.KeyboardButton('💰 Баланс')
wallet_button = types.KeyboardButton('💼 Кошелек')
info_button = types.KeyboardButton('🐇 О проекте')
tasks_button = types.KeyboardButton('💸 Задания')
claim_button = types.KeyboardButton('🎁 Получить $NEMR')
USER_MARKUP.add(balance_button, wallet_button)
USER_MARKUP.add(info_button, tasks_button)
USER_MARKUP.add(claim_button)


USER_MARKUP_EN = types.ReplyKeyboardMarkup(resize_keyboard=True)
en_balance_button = types.KeyboardButton('💰 Balance')
en_wallet_button = types.KeyboardButton('💼 Wallet')
en_info_button = types.KeyboardButton('🐇 About')
en_tasks_button = types.KeyboardButton('💸 Tasks')
en_claim_button = types.KeyboardButton('🎁 Claim $NEMR')
USER_MARKUP_EN.add(en_balance_button, en_wallet_button)
USER_MARKUP_EN.add(en_info_button, en_tasks_button)
USER_MARKUP_EN.add(en_claim_button)


balance_commands = [balance_button.text, en_balance_button.text]
wallet_commands = [wallet_button.text, en_wallet_button.text]
info_commands = [info_button.text, en_info_button.text]
tasks_commands = [tasks_button.text, en_tasks_button.text]
claim_commands = [claim_button.text, en_claim_button.text]