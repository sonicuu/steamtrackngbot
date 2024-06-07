from flask import Flask, request
from Controllers.price_tracker import get_price
from Controllers.inventory_parse import inventory
from Controllers.steam_parse import resolve_vanity_url


app = Flask(__name__)

app.add_url_rule('/get_price', 'get_price', get_price, methods=['GET'])
app.add_url_rule('/inventory', 'inventory', inventory, methods=['GET'])
app.add_url_rule('/resolve_vanity_url', 'resolve_vanity_url', resolve_vanity_url, methods=['GET'])

if __name__ == '__main__':
    app.run(debug=True)




