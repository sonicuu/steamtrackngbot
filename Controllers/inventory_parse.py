from flask import Flask, jsonify, request
import requests

app = Flask(__name__)


class InventoryParse:
    @staticmethod
    def get_inventory(steam_id, id_game):
        url = f'https://steamcommunity.com/inventory/{steam_id}/{id_game}/2?count=5000'
        response = requests.get(url)
        list_item = []

        if response.status_code == 200:
            items = []
            response_obj = response.json()
            for asset in response_obj['assets']:
                for description in response_obj['descriptions']:
                    if asset['classid'] == description['classid']:
                        items.append({'item': asset['classid'], 'description': description, 'asset': asset})
                        break

            for item in items:
                name = item['description']['market_hash_name']
                marketable = bool(item['description']['marketable'])
                if marketable:
                    list_item.append(name)

        elif response.status_code == 429:
            return 'Слишком много запросов', 429

        else:
            return 'Ошибка при запросе к Steam', 500

        return list(set(list_item)), 200

    @staticmethod
    def get_unique_items(steam_id, id_game):
        url = f'https://steamcommunity.com/inventory/{steam_id}/{id_game}/2?count=5000'
        response = requests.get(url)
        unique_items = []

        if response.status_code == 200:
            response_obj = response.json()
            for asset in response_obj['assets']:
                for description in response_obj['descriptions']:
                    if asset['classid'] == description['classid']:
                        unique_items.append(
                            {'item': asset['classid'], 'description': description['market_hash_name'], 'asset': asset})
                        break
        return unique_items


@app.route('/inventory', methods=['GET'])
def inventory():
    steam_id = request.args.get('steam_id')
    id_game = request.args.get('id_game')

    if not steam_id or not id_game:
        return jsonify({'error': 'Необходимо указать steam_id и id_game'}), 400

    items, status_code = InventoryParse.get_inventory(steam_id, id_game)
    if status_code == 200:
        return jsonify({'items': items})
    else:
        return jsonify({'error': items}), status_code





