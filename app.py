from flask import Flask, request, render_template_string, redirect
import csv
import math
import os

app = Flask(__name__)

# Dolar kuru
DOLAR_KURU = 38.9  # Örneğin 1 USD = 38 TL
PRICE_UPDATE_DATE = "2025-05-04"

TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Card Price Checker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 30px;
            background-color: #f2f2f2;
        }
        h1 {
            color: #333;
        }
        form {
            margin-bottom: 20px;
        }
        input[type=text] {
            padding: 8px;
            width: 300px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        input[type=submit], select {
            padding: 8px 15px;
            border: none;
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type=submit]:hover {
            background-color: #45a049;
        }
        .filter-box {
            position: absolute;
            top: 30px;
            right: 30px;
            background-color: #ffffff;
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .filter-box form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .filter-box label {
            font-weight: bold;
        }

        .filter-box select {
            padding: 5px;
            border-radius: 5px;
        }

        .cards-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
            justify-content: flex-start;
        }
        .card {
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 180px;
            height: 320px;
            overflow: hidden;
            transition: all 0.3s ease;
            position: relative;
        }
        .in-stock {
            position: absolute;
            top: 10px;
            left: -35px;
            transform: rotate(-45deg);
            background-color: green;
            color: white;
            font-weight: bold;
            padding: 5px 40px;
            font-size: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 10;
        }

        .out-of-stock {
            position: absolute;
            top: 10px;
            left: -35px;
            transform: rotate(-45deg);
            background-color: red;
            color: white;
            font-weight: bold;
            padding: 5px 40px;
            font-size: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 10;
        }

        .multiplier-badge {
            position: absolute;
            top: 0px;
            left: -40px;
            transform: rotate(-45deg);
            background-color: gold;
            color: black;
            font-weight: bold;
            padding: 5px 40px;
            font-size: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 10;
        }

        .card:hover {
            transform: scale(1.05);
        }
        .card img {
            width: 100%;
            height: 65%;
            object-fit: contain;
            border-radius: 4px;
            margin-bottom: 10px;
            background-color: white;
        }
        .card-name {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .card-price, .card-stock {
            color: #333;
            font-size: 13px;
            font-weight: bold;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }
        .page-button {
            display: inline-block;
            padding: 10px 20px;
            text-decoration: none;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            color: #4CAF50;
            transition: all 0.3s ease;
        }
        .page-button:hover {
            background-color: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>

<h1>Card Price Checker (V23)</h1>

<h2>Enter a card name:</h2>
<form method="post">
  <input name="card" type="text" placeholder="Example: Charizard GX" value="{{ card }}">
  <input type="submit" value="Check">
</form>

<div class="filter-box">
    <form method="post">
        <label>Stock:</label>
        <select name="stock">
            <option value="">All</option>
            <option value="in" {% if selected_stock == 'in' %}selected{% endif %}>In Stock</option>
            <option value="out" {% if selected_stock == 'out' %}selected{% endif %}>Out of Stock</option>
        </select>

        <label>Set:</label>
        <select name="set">
            <option value="">All Sets</option>
            {% for s in sets %}
                <option value="{{ s }}" {% if s == selected_set %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
        </select>

        <input type="hidden" name="card" value="{{ card }}">
        <input type="submit" value="Apply">
    </form>
</div>


{% if prices %}
    <h3>Results:</h3>
    <div class="cards-container">
    {% for card in prices %}
        <div class="card">
            {% if card.stock == 0 %}
                <div class="out-of-stock">Stokta Yok</div>
            {% else %}
                <div class="in-stock">Stokta Var</div>
            {% endif %}
            <div class="multiplier-badge">{{ card.multiplier_text }}</div>
            <img src="{{ card.image }}" alt="Card Image">
            <div class="card-name">{{ card.name }}</div>
            <div class="card-price">{{ card.price }} TL</div>
            <div class="card-stock">Stock: {{ card.stock }}</div>
        </div>
    {% endfor %}
    </div>

    {% if total_pages > 1 %}
    <div class="pagination">
    {% if page > 1 %}
        <a class="page-button" href="/?card={{ card }}&stock={{ selected_stock }}&set={{ selected_set }}&page={{ page - 1 }}">⟵ Previous</a>
    {% endif %}
    {% if page < total_pages %}
        <a class="page-button" href="/?card={{ card }}&stock={{ selected_stock }}&set={{ selected_set }}&page={{ page + 1 }}">Next ⟶</a>
    {% endif %}
    </div>
    {% endif %}

{% elif price %}
    <h3>{{ price }}</h3>
{% endif %}

</body>
</html>
'''


def get_price(card_name, stock_filter=None, set_filter=None):
    try:
        found_cards = []
        unique_sets = set()

        stock_data = {}
        with open('stock.csv', mode='r', encoding='utf-8') as stock_file:
            stock_reader = csv.DictReader(stock_file, delimiter=',')
            for s_row in stock_reader:
                set_name = s_row['set-name'].strip().lower()
                card_code = s_row['card-code'].strip().lower()
                quantity = int(s_row['stock-quantity'])
                stock_data[(set_name, card_code)] = quantity

        with open('collection.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                product_name = row['product-name'].strip()
                set_name = row['console-name'].strip().replace('Pokemon ', '').strip().lower()
                unique_sets.add(set_name.title())

                card_code = ''
                if '#' in product_name:
                    card_code = product_name.split('#')[-1].split(',')[0].strip().lower()

                if card_name.strip() == "" or card_name.strip().lower() in product_name.lower():
                    stock_amount = stock_data.get((set_name, card_code), 0)

                    if stock_filter == "in" and stock_amount == 0:
                        continue
                    if stock_filter == "out" and stock_amount > 0:
                        continue
                    if set_filter and set_name.title() != set_filter:
                        continue

                    try:
                        price_in_dollars = int(row['price-in-pennies']) / 100
                    except:
                        price_in_dollars = 0

                    # Çarpan hesapla
                    if price_in_dollars > 100:
                        multiplier = 1.4
                    elif price_in_dollars > 50:
                        multiplier = 1.5
                    else:
                        multiplier = 1.6

                    price_in_tl = price_in_dollars * DOLAR_KURU * multiplier
                    rounded_price = math.ceil(price_in_tl / 5) * 5
                    multiplier_text = f"x{multiplier:.1f}"

                    image_filename = product_name.lower().replace(' ', '-').replace('#', '').replace('[', '').replace(
                        ']', '').replace('/', '-') + '.png'
                    image_path = f"/static/images_small/{image_filename}"
                    if not os.path.exists('static/images_small/' + image_filename):
                        image_path = "/static/images/no-image.png"

                    found_cards.append({
                        'name': product_name,
                        'price': rounded_price,
                        'stock': stock_amount,
                        'image': image_path,
                        'multiplier_text': multiplier_text
                    })

        if found_cards:
            return found_cards, sorted(unique_sets)
        else:
            return "Card not found", sorted(unique_sets)

    except Exception as e:
        print("[ERROR]", e)
        return "Error", []


@app.route('/', methods=['GET', 'POST'])
def index():
    prices = None
    price = None
    sets = []
    card = request.args.get('card', "").strip()
    stock = request.args.get('stock', "").strip()
    set_filter = request.args.get('set', "").strip()
    page = int(request.args.get('page', 1))
    per_page = 20

    if request.method == 'POST':
        card = request.form.get('card', "")
        stock = request.form.get('stock', "")
        set_filter = request.form.get('set', "")
        return redirect(f"/?card={card}&stock={stock}&set={set_filter}&page=1")

    result, sets = get_price(card, stock, set_filter)
    if isinstance(result, list):
        total_pages = math.ceil(len(result) / per_page)
        start = (page - 1) * per_page
        end = start + per_page
        prices = result[start:end]
    else:
        price = result
        total_pages = 1

    return render_template_string(
        TEMPLATE,
        prices=prices,
        price=price,
        card=card,
        page=page,
        sets=sets,
        selected_stock=stock,
        selected_set=set_filter,
        total_pages=total_pages
    )


if __name__ == '__main__':
    app.run(debug=True)
