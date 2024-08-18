from telebot import types

import config


USER_MARKUP = types.ReplyKeyboardMarkup(resize_keyboard=True)
balance_button = types.KeyboardButton('💰 Баланс')
wallet_button = types.KeyboardButton('💼 Кошелек')
info_button = types.KeyboardButton('🌳 О проекте')
tasks_button = types.KeyboardButton('📋 Задания')
claim_button = types.KeyboardButton(f'🎁 Получить {config.COIN_NAME}')
buy_button = types.KeyboardButton(f'💸 Купить {config.COIN_NAME}')
USER_MARKUP.add(balance_button, wallet_button)
USER_MARKUP.add(info_button, tasks_button)
USER_MARKUP.add(claim_button)
USER_MARKUP.add(buy_button)


USER_MARKUP_EN = types.ReplyKeyboardMarkup(resize_keyboard=True)
en_balance_button = types.KeyboardButton('💰 Balance')
en_wallet_button = types.KeyboardButton('💼 Wallet')
en_info_button = types.KeyboardButton('🌳 About')
en_tasks_button = types.KeyboardButton('📋 Tasks')
en_claim_button = types.KeyboardButton(f'🎁 Claim {config.COIN_NAME}')
en_buy_button = types.KeyboardButton(f'💸 Buy {config.COIN_NAME}')
USER_MARKUP_EN.add(en_balance_button, en_wallet_button)
USER_MARKUP_EN.add(en_info_button, en_tasks_button)
USER_MARKUP_EN.add(en_claim_button)
USER_MARKUP_EN.add(en_buy_button)


balance_commands = [balance_button.text, en_balance_button.text]
wallet_commands = [wallet_button.text, en_wallet_button.text]
info_commands = [info_button.text, en_info_button.text]
tasks_commands = [tasks_button.text, en_tasks_button.text]
claim_commands = [claim_button.text, en_claim_button.text]
buy_commands = [buy_button.text, en_buy_button.text]
