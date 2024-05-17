import re
from telebot import types
import telebot
import requests

bot = telebot.TeleBot("7158930139:AAEtyFtt60Ioh5ZR1bBFwxcRI0vJtH7mpuU");
steam_id = 0
id_game = 0

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Здравстуйте, отправьте ссылку на ваш профиль стим. Предварительно откройте свой инвентарь стим.")
    bot.register_next_step_handler(message, check_message_for_url)



def check_message_for_url(message):
    global steam_id
    url_pattern = re.compile(r'https?://steamcommunity.com/\S+')
    url_list = list(filter(None, str(message.text).split('/')))
    print(url_list)

    url = re.search(url_pattern, message.text)
    if url:
        bot.reply_to(message, "Вы ввели ссылку на аккаунт стим!")

        if url_list[-2] == "id":
            # Отправляем HTTP запрос к Flask контроллеру
            response = requests.get(f'http://127.0.0.1:5000/resolve_vanity_url?vanity_url={url_list[-1]}')
            if response.status_code == 200:
                steam_id = response.json().get('steam_id')
                print(f"SteamID: {steam_id}")
            else:
                bot.reply_to(message, "Ошибка при получении SteamID")

        elif url_list[-2] == "profiles":
            steam_id = url_list[-1]
            print(url_list[-1])

        bot.register_next_step_handler(message, game_keyboard)
        game_keyboard(message)

    else:
        bot.reply_to(message, "Это не ссылка на аккаунт стим.")



def game_keyboard(message):

    keyboard = types.InlineKeyboardMarkup();
    key_cs = types.InlineKeyboardButton(text='Counter-Strike 2', callback_data='cs');
    key_dota = types.InlineKeyboardButton(text='Dota 2', callback_data='dota');
    key_tf = types.InlineKeyboardButton(text='Team Fortress 2', callback_data='tf');
    key_rust = types.InlineKeyboardButton(text='Rust', callback_data='rust');

    keyboard.add(key_cs);
    keyboard.add(key_dota);
    keyboard.add(key_tf);
    keyboard.add(key_rust);
    bot.send_message(message.from_user.id, text='Какую игру вы бы хотели отслеживать?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global id_game
    if call.data == 'cs':
        id_game = 730
    elif call.data == 'dota':
        id_game = 570
    elif call.data == 'tf':
        id_game = 440
    elif call.data == 'rust':
        id_game = 252490

    bot.answer_callback_query(call.id, "Выбор сделан")

    game_choice(call.message)
    bot.register_next_step_handler(call.message, game_choice)


def item_keyboard(steam_id, id_game):
    keyboard = types.InlineKeyboardMarkup()
    # Отправляем HTTP запрос к Flask контроллеру
    response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')
    if response.status_code == 200:
        list_item = response.json().get('items', [])
        for k, item_name in enumerate(list_item, 1):
            keyboard.add(types.InlineKeyboardButton(text=item_name, callback_data=f'btn_game_{k}'))
        return keyboard
    else:
        print(f"Ошибка при получении инвентаря: {response.status_code}")
        return None



@bot.message_handler()
def game_choice(message):
    global steam_id, id_game
    keyboard = item_keyboard(steam_id, id_game)
    bot.send_message(message.chat.id, 'Выберитеtt один или несколько вариантов:', reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_query)


selected_items = []

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    print('РИВАВЫАФЫВАЫВАЫВАЫВАваьожвфоджфаожывфоаджфывоажвоыфжбдаофжывдоажывдоажфыв')
    global selected_items
    # Проверяем, что callback_data начинается с 'btn_game_'
    response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')
    if response.status_code == 200:
        list_item = response.json().get('items', [])
    if call.data.startswith('btn_game_'):
        # Получаем индекс предмета
        item_index = int(call.data.split('_')[-1]) - 1
        # Добавляем предмет в массив selected_items
        selected_items.append(list_item[item_index])
        # Отправляем уведомление пользователю о выбранном предмете
        bot.answer_callback_query(call.id, f'Вы выбрали: {list_item[item_index]}')
        print(f'Вы выбрали: {list_item[item_index]}')




bot.polling(none_stop=True)