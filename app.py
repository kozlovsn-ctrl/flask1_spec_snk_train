import random
from flask import Flask
from flask import request

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
побеждает."""
},
{
"id": 5,
"author": "Waldi Ravens",
"text": """Программирование на С похоже на быстрые танцы
на только что отполированном полу людей с острыми бритвами в
руках."""
},
{
"id": 6,
"author": "Mosher’s Law of Software Engineering",
"text": """Не волнуйтесь, если что-то не работает. Если
бы всё работало, вас бы уволили."""
},
{
"id": 8,
"author": "Yoggi Berra",
"text": """В теории, теория и практика неразделимы. На
практике это не так."""
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
    quotes_by_id = {quote["id"]: quote for quote in quotes}
    if quotes_by_id:
        max_id = max(quotes_by_id.keys())
    else:
        max_id = 0
    return max_id+1

#Меняем содержимое цитаты по id
def update_quote_by_id(quotes_list, quote_id, new_author, new_text):
    for quote in quotes_list:
        if quote["id"] == quote_id:
            quote["author"] = new_author
            quote["text"] = new_text
            return True
    return False    

#Полный список цитат
@app.route("/quotes/")
def quotes_list():
    return quotes

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
        return f"Цитата с id={quote_id} не найдена", 404
    return quote

#Вносим новую цитату
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    new_id = get_new_quote_id (quotes)
    new_quote = {"id": new_id, **data}
    quotes.append(new_quote) 
    return get_quote_by_id(quotes, new_id), 201

#Изменяем существующую цитату
@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.json
    quote = get_quote_by_id (quotes, id)
    if quote is not None:
        if "author" in new_data:
            new_author = new_data["author"]
        else:
            new_author = quote["author"]
        if "text" in new_data:
            new_text = new_data["text"]
        else:
            new_text = quote["text"]
        update_quote_by_id(quotes, id, new_author, new_text)
        quote = get_quote_by_id (quotes, id)
        result_code = '200'
    else:
        result_code = '404'
        quote = {}
    return quote, result_code

#Удаляем указанную цитату
@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete(id):
    global quotes  
    for i, quote in enumerate(quotes):
        if quote["id"] == id:
            quotes.pop(i)
            return f"Цитата с id={id} удалена.", 200
    return f"Цитата с id={id} не найдена.",404
    

if __name__ == "__main__":
    app.run(debug=True)