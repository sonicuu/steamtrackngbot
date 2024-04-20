from flask import Flask, jsonify, request
from steam_community_market import Market

app = Flask(__name__)

@app.route('/get_price', methods=['GET'])
def get_price():
    item_name = request.args.get('item_name')
    app_id = request.args.get('app_id')
    if not item_name or not app_id:
        return jsonify({'error': 'Недостаточно параметров запроса'}), 400

    try:
        app_id = int(app_id)  # Преобразование app_id в целое число
    except ValueError:
        return jsonify({'error': 'app_id должен быть целым числом'}), 400

    try:
        market = Market("RUB")
        lowest_price = market.get_lowest_price(item_name, app_id)
        return jsonify({'item_name': item_name, 'lowest_price': lowest_price})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



