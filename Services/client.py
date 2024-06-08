import re
from telebot import types
import telebot
import requests
import random
import time
import threading
from Services.users import Users


bot = telebot.TeleBot("7158930139:AAEtyFtt60Ioh5ZR1bBFwxcRI0vJtH7mpuU");
user_stop_flags = {}
# user_stop_flags = {id: [stop_flag, is_query_handler_active]}

serviceUser = Users()


@bot.message_handler(commands=['start'])
def handle_start(message):
    global user_stop_flags
    menu(message)
    if serviceUser.get_user_data(message.chat.id) != (None, None, None, []):
        serviceUser.delete_user_data(message.chat.id)


    user_stop_flags[message.chat.id] = [False, True]
    bot.register_next_step_handler(message, check_message_for_url)

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    global user_stop_flags
    if user_stop_flags!={}:
        user_stop_flags[message.chat.id][0] = False
        print(user_stop_flags)
        bot.send_message(message.chat.id, "Бот остановлен. Для начала новой сессии используйте команду /start.")

def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton('Старт')
    btn_stop = types.KeyboardButton('Стоп')
    markup.add(btn_start, btn_stop)
    bot.send_message(message.chat.id, text="Здравстуйте, отправьте ссылку на ваш профиль стим. Предварительно откройте свой инвентарь стим.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'Старт':
        handle_start(message)
    elif message.text == 'Стоп':
        handle_stop(message)



def check_message_for_url(message):
    global user_stop_flags

    _, steam_id, _, _ = serviceUser.get_user_data(message.chat.id)

    url_pattern = re.compile(r'https?://steamcommunity.com/\S+')
    url_list = list(filter(None, str(message.text).split('/')))

    url = re.search(url_pattern, message.text)
    if url:
        bot.reply_to(message, "Вы ввели ссылку на аккаунт стим!")

        if url_list[-2] == "id":
            # Отправляем HTTP запрос к Flask контроллеру
            response = requests.get(f'http://127.0.0.1:5000/resolve_vanity_url?vanity_url={url_list[-1]}')
            if response.status_code == 200:
                steam_id = response.json().get('steam_id')
                serviceUser.save_user_data(message.chat.id, steam_id, None, None)
            else:
                bot.reply_to(message, "Ошибка при получении SteamID")

        elif url_list[-2] == "profiles":
            steam_id = url_list[-1]
            serviceUser.save_user_data(message.chat.id, steam_id, None, None)
            print(url_list[-1])

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
    bot.send_message(message.chat.id, text='Какую игру вы бы хотели отслеживать?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global user_stop_flags
    # Проверяем, активен ли обработчик
    if not user_stop_flags[call.message.chat.id][1]:

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
    chat_id, steam_id, _, _ = serviceUser.get_user_data(call.message.chat.id)
    serviceUser.save_user_data(chat_id, steam_id, id_game, None)

    bot.delete_message(call.message.chat.id, call.message.message_id)
    # bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    user_stop_flags[call.message.chat.id][1] = False
    display_inventory(call.message)
    # Деактивируем обработчик после вызова display_inventory


def display_inventory(message):
    global user_stop_flags
    _, steam_id, id_game, _ = serviceUser.get_user_data(message.chat.id)
    response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')

    if response.status_code == 200 and response.json()['items']!=[]:

        inventory_items = response.json().get('items', [])
        inventory_items = [f"{i+1}. {k}\n" for i,k in enumerate(inventory_items)]
        inventory_text = ""
        arr = []
        for i in inventory_items:
            if len(inventory_text+i)>4096:
                arr.append(inventory_text)
                inventory_text = ""
            inventory_text+=i
            if i == inventory_items[-1]:
                arr.append(inventory_text)
        {bot.send_message(chat_id=message.chat.id, text=i) for i in arr}


        bot.register_next_step_handler(message, handle_item_selection)
        bot.send_message(message.chat.id, "Выберите предметы из инвентаря, введя их номера через запятую:\n")
    else:
        bot.send_message(message.chat.id, "Инвентарь данной игры пуст.")
        user_stop_flags[message.chat.id][1] = True
        game_keyboard(message)


def handle_item_selection(message):
    global user_stop_flags
    _, steam_id, id_game, _ = serviceUser.get_user_data(message.chat.id)
    # Разбираем введенные пользователем индексы и сохраняем выбранные предметы
    try:
        selected_indices = [int(index.strip()) for index in message.text.split(',')]
        selected_indices = list(set(selected_indices))
        response = requests.get(f'http://127.0.0.1:5000/inventory?steam_id={steam_id}&id_game={id_game}')
        if response.status_code == 200:
            inventory_items = response.json().get('items', [])
            if selected_indices[0] > len(inventory_items):
                bot.send_message(message.chat.id, f'Вы ввели неправильный(ые) индекс(ы)!')
                user_stop_flags[message.chat.id][0] = False
            else:
                selected_items = [inventory_items[index-1] for index in selected_indices if 0 < index <= len(inventory_items)]
                selected_items_text = "Вы выбрали следующие предметы:\n" + "\n".join(selected_items)
                bot.send_message(message.chat.id, selected_items_text)
                selected_price_items = []
                for item in selected_items:
                    response = requests.get(f'http://127.0.0.1:5000/get_price?item_name={item}&app_id={id_game}')
                    price_info = response.json()
                    selected_price_items.append(f"{price_info['item_name']}_{price_info['lowest_price']}")
                    serviceUser.save_user_data(message.chat.id, steam_id, id_game, ";".join(selected_price_items))

        else:
            bot.send_message(message.chat.id, "Ошибка при получении инвентаря.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректные номера предметов.")
    user_stop_flags[message.chat.id][0] = True
    send_prices(message)

# Функция для отправки цен на выбранные предметы
def send_prices(message):
    global user_stop_flags
    _, _, id_game, selected_items = serviceUser.get_user_data(message.chat.id)

    try:
        if selected_items != None:
            selected_items = selected_items.split(';')
            selected_items = [i.split("_") for i in selected_items]
            print(selected_items)
            for i in selected_items:
                i[1]=i[1].replace(",", ".", 1)
                i[1]=float(i[1].replace(" pуб.", "", 1))

            items_dict = {item[0]: item[1] for item in selected_items}

        print(items_dict)
    except UnboundLocalError:
        bot.send_message(message.chat.id, f'Попробуйте еще раз (команда Старт).')
        user_stop_flags[message.chat.id][0] = False
    while True:
        if not user_stop_flags[message.chat.id][0]:
            break
        try:
            # Случайная задержка от 16 до 32 секунд
            time.sleep(random.randint(5, 6))

            for item, value in items_dict.items():
                print(item, value)
                # Запрос к контроллеру Flask для получения цены предмета
                response = requests.get(f'http://127.0.0.1:5000/get_price?item_name={item}&app_id={id_game}')
                if response.status_code == 200 and user_stop_flags[message.chat.id][0]:
                    old_price = value
                    new_price_request = response.json()
                    new_price = new_price_request['lowest_price']
                    new_price = new_price.replace(",", ".", 1)
                    new_price = float(new_price.replace(" pуб.", "", 1))
                    if ((new_price - old_price) / old_price) * 100 >= 10:
                        bot.send_message(message.chat.id,
                                         f"Поздравляем! Цена вашего предмета {item} увеличилась c {old_price} руб. до {new_price} руб. ({new_price-old_price} руб. прибыли)")
                        items_dict[item] = new_price
                    elif ((new_price - old_price) / old_price) * 100 <= -10:
                        bot.send_message(message.chat.id,
                                         f"Сожалеем... Цена предмета {item} уменьшилась c {old_price} руб. до {new_price} руб. ({abs(new_price-old_price)} руб. убытков)")
                        items_dict[item] = new_price
                    else:
                        bot.send_message(message.chat.id,
                                         f"Тест: Цена предмета {item}: старая ({old_price}), новая ({new_price}), разница ({abs(new_price - old_price)})")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


bot.polling(none_stop=True)