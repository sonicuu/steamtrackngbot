from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/resolve_vanity_url', methods=['GET'])
def resolve_vanity_url():
    vanity_url = request.args.get('vanity_url')
    api_key = "F9FD7DE3C7CA2089C9D77F05C76C3642"
    if not vanity_url:
        return jsonify({'error': 'Необходимо указать vanity_url '}), 400

    base_url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
    params = {'key': api_key, 'vanityurl': vanity_url}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['response']['success'] == 1:
            steam_id = data['response']['steamid']
            return jsonify({'steam_id': steam_id})
        else:
            return jsonify({'error': 'Не удалось преобразовать пользовательский URL в SteamID'}), 404
    else:
        return jsonify({'error': 'Ошибка при запросе к Steam API'}), response.status_code


