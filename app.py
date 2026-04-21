import random
from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False

@app.route("/")
def hello_world():
    return "Hello, World!"

about_me = {
"name": "Сергей",
"surname": "Козлов",
"email": "kozlov.sn@gmail.com"
}

@app.route("/about")
def about():
    return about_me

quotes = [
{
"id": 3,
"author": "Rick Cook",
"text": """Программирование сегодня — это гонка
разработчиков программ, стремящихся писать программы с
большей и лучшей идиотоустойчивостью, и вселенной, которая
пытается создать больше отборных идиотов. Пока вселенная
побеждает.""",
"rating": 5
},
{
"id": 5,
"author": "Waldi Ravens",
"text": """Программирование на С похоже на быстрые танцы
на только что отполированном полу людей с острыми бритвами в
руках.""",
"rating": 3
},
{
"id": 6,
"author": "Mosher’s Law of Software Engineering",
"text": """Не волнуйтесь, если что-то не работает. Если
бы всё работало, вас бы уволили.""",
"rating": 4
},
{
"id": 8,
"author": "Yoggi Berra",
"text": """В теории, теория и практика неразделимы. На
практике это не так.""",
"rating": 2
},
]

#Получаем цитату по id
def get_quote_by_id(quotes, target_id):
    for quote in quotes:
        if quote["id"] == target_id:
            return quote
    return None

#Новый id для вставки
def get_new_quote_id (quotes):
    return max((quote["id"] for quote in quotes), default=0) + 1

#Меняем содержимое цитаты по id
def update_quote_by_id_(quotes_list, quote_id, new_author, new_text, new_rating):
    for quote in quotes_list:
        if quote["id"] == quote_id:
            quote["author"] = new_author
            quote["text"] = new_text
            quote["rating"] = new_rating
            return True
    return False    

def update_quote_by_id(quotes_list, quote_id, new_data):
    for quote in quotes_list:
        if quote["id"] == quote_id:
            if "rating" in new_data and not (1 <= new_data["rating"] <= 5):
                new_data.pop("rating")  
            quote.update(new_data)
            return quote
    return None    

#Полный список цитат
@app.route("/quotes/")
def quotes_list():
    return quotes

#Полный список цитат
@app.route("/quotes/filter")
def filtered_quotes_list():
    found_quotes = []
    args = request.args
    arg_author = args.get('author')
    arg_rating = args.get('rating')
    for quote in quotes:
        if (((arg_author is not None) 
           and (arg_rating is not None) 
           and (quote["author"] == arg_author)
           and (quote["rating"] == int(arg_rating)))
           or
           ((arg_author is not None) 
           and (arg_rating is None) 
           and (quote["author"] == arg_author))
           or
           ((arg_author is None) 
           and (arg_rating is not None) 
           and (quote["rating"] == int(arg_rating)))):
            found_quotes.append(quote)
    return found_quotes


#Пересчитываем наличные цитаты
@app.route("/quotes/count")
def quotes_count():
    quotes_num = {"count": len(quotes)}
    return quotes_num

#Цитируем случайно
@app.route("/quotes/random")
def quotes_rnd():
    random_quote = random.choice(quotes)
    return random_quote

#Выдаём цитату по id
@app.route("/quotes/<int:quote_id>")
def quote_get_by_id(quote_id):
    quote = get_quote_by_id (quotes, quote_id)
    if quote is None:
        return jsonify({"message": f"Цитата с id={quote_id} не найдена"}), 404
    return quote

#Вносим новую цитату
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    new_id = get_new_quote_id (quotes)
    if "rating" in data:
        if  1 <= data["rating"] <= 5:
            new_quote = {"id": new_id, **data}
        else:
            new_quote = {"id": new_id, 
                         "author": data["author"], 
                         "text": data["text"],
                         "rating": 1}
    else:
        new_quote = {"id": new_id, **data, "rating": 1}
    quotes.append(new_quote) 
    return get_quote_by_id(quotes, new_id), 201

#Изменяем существующую цитату
@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.json
    allowed_fields = {"author", "text", "rating"}
    filtered_data = {k: v for k, v in new_data.items() if k in allowed_fields}
    updated_quote = update_quote_by_id(quotes, id, filtered_data)
    if updated_quote is None:
        return {}, 404
    return updated_quote, 200

#Удаляем указанную цитату
@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete(id):
    global quotes  
    for i, quote in enumerate(quotes):
        if quote["id"] == id:
            quotes.pop(i)
            return jsonify({"message": f"Цитата с id={id} удалена."}), 200
    return jsonify({"message": f"Цитата с id={id} не найдена."}), 404
    

if __name__ == "__main__":
    app.run(debug=True)