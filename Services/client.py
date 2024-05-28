import re
from telebot import types
import telebot
import requests
import random
import time
import threading


bot = telebot.TeleBot("7158930139:AAEtyFtt60Ioh5ZR1bBFwxcRI0vJtH7mpuU");
steam_id = 0
id_game = 0
selected_items = []

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

is_query_handler_active = True

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global id_game, is_query_handler_active
    # Проверяем, активен ли обработчик
    if not is_query_handler_active:
        return  # Прекращаем обработку, если обработчик неактивен

    if call.data == 'cs':
        id_game = 730
    elif call.data == 'dota':
        id_game = 570
    elif call.data == 'tf':
        id_game = 440
    elif call.data == 'rust':
        id_game = 252490

    bot.answer_callback_query(call.id, "Выбор сделан")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    is_query_handler_active = False
    display_inventory(call.message)
    # Деактивируем обработчик после вызова display_inventory


def display_inventory(message):
    global steam_id, id_game
    response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')
    if response.status_code == 200:
        inventory_items = response.json().get('items', [])
        inventory_text = "Выберите предметы из инвентаря, введя их номера через запятую:\n"
        inventory_text += "\n".join(f"{index+1}. {item}" for index, item in enumerate(inventory_items))
        bot.send_message(message.chat.id, inventory_text)
        bot.register_next_step_handler(message, handle_item_selection)
    else:
        bot.send_message(message.chat.id, "Ошибка при получении инвентаря.")

def handle_item_selection(message):
    global selected_items
    # Разбираем введенные пользователем индексы и сохраняем выбранные предметы
    try:
        selected_indices = [int(index.strip()) for index in message.text.split(',')]
        response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')
        if response.status_code == 200:
            inventory_items = response.json().get('items', [])
            selected_items = [inventory_items[index-1] for index in selected_indices if 0 < index <= len(inventory_items)]
            selected_items_text = "Вы выбрали следующие предметы:\n" + "\n".join(selected_items)
            bot.send_message(message.chat.id, selected_items_text)
        else:
            bot.send_message(message.chat.id, "Ошибка при получении инвентаря.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректные номера предметов.")
    # Запуск потока для отправки цен
    price_thread = threading.Thread(target=send_prices, args=(message,))
    price_thread.start()

# Функция для отправки цен на выбранные предметы
def send_prices(message):
    while True:
        try:
            # Случайная задержка от 16 до 32 секунд
            time.sleep(random.randint(16, 32))
            for item in selected_items:
                # Запрос к контроллеру Flask для получения цены предмета
                response = requests.get(f'http://127.0.0.1:5000/get_price?item_name={item}&app_id={id_game}')
                if response.status_code == 200:
                    price_info = response.json()
                    bot.send_message(message.chat.id, f"Цена на '{price_info['item_name']}': {price_info['lowest_price']}")
                else:
                    bot.send_message(message.chat.id, "Ошибка при получении цены предмета.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")





bot.polling(none_stop=True)