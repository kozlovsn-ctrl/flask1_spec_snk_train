import random
from flask import Flask, request, jsonify, g
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "store.db"  # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False

# Цитаты из списка 1-го дня перенесены в таблицу, 
# которая создана скриптом sqlite_examples/sql_create_table.py
# Внесение скриптом sqlite_examples/sql_create_quotes.py

################################ Вспомогательное ################################

# Подключаем БД
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Преобразовываем в список словарей
def quotes_repack (quotes_db):
    keys = ("id", "author", "text", "rating")
    quotes = []
    for quote_db in quotes_db:
        quote = dict(zip(keys, quote_db))
        quotes.append(quote)
    return quotes

################################ Обработчики ################################

# Полный список цитат
@app.route("/quotes/")
def quotes_list():
    cursor = get_db().cursor()
    db_request = "SELECT * FROM quotes"
    cursor.execute(db_request)
    quotes_db = cursor.fetchall()
    quotes = quotes_repack (quotes_db)
    return jsonify(quotes), 200

# Пересчитываем наличные цитаты
@app.route("/quotes/count")
def quotes_count():
    cursor = get_db().cursor()
    db_request = "SELECT COUNT(*) AS num FROM quotes"
    cursor.execute(db_request)
    db_result = cursor.fetchone()
    quotes_num = {"count": db_result["num"]}
    return quotes_num

# Цитируем случайно
@app.route("/quotes/random")
def quotes_rnd():
    cursor = get_db().cursor()
    db_request = "SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1"
    cursor.execute(db_request)
    db_result = cursor.fetchone()    
    if db_result:
        return jsonify(dict(db_result)), 200
    return jsonify({"Ошибка": "Мешок с цитатами пуст"}), 404

# Выдаём цитату по id
@app.route("/quotes/<int:quote_id>")
def quote_get_by_id(quote_id):
    cursor = get_db().cursor()
    db_request = "SELECT * FROM quotes WHERE id = ?"
    cursor.execute(db_request, (quote_id,))
    db_result = cursor.fetchone()    
    if db_result:
        return jsonify(dict(db_result)), 200
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Вносим новую цитату
@app.route("/quotes", methods=['POST'])
def create_quote():
    connection = get_db()
    cursor = connection.cursor()
    data = request.json
    if "rating" in data:
        if  1 <= data["rating"] <= 5:
            new_quote = {**data}
        else:
            new_quote = {"author": data["author"], 
                         "text": data["text"],
                         "rating": 1}
    else:
        new_quote = {**data, "rating": 1}
    db_request = "INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?)"
    cursor.execute(db_request, (new_quote["author"], new_quote["text"], new_quote["rating"]))   
    connection.commit() 
    new_id = cursor.lastrowid
    res_quote = {"id": new_id, **new_quote}
    return res_quote, 201

# Удаляем указанную цитату
@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
    connection = get_db()
    cursor = connection.cursor()
    db_request = "DELETE FROM quotes WHERE id = ?"
    cursor.execute(db_request, (quote_id,))
    connection.commit()
    if cursor.rowcount:
        return jsonify({"message": f"Цитата с id={quote_id} удалена."}), 200
    return jsonify({"message": f"Цитата с id={quote_id} не найдена."}), 404

# Изменяем существующую цитату
@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    connection = get_db()
    cursor = connection.cursor()
    db_request = "SELECT * FROM quotes WHERE id = ?"
    cursor.execute(db_request, (quote_id,))
    db_result = cursor.fetchone()    
    if db_result:
        upd_data = dict(db_result)
        new_data = request.json
        allowed_fields = {"author", "text", "rating"}
        filtered_data = {k: v for k, v in new_data.items() if k in allowed_fields}
        if "rating" in filtered_data and not (1 <= new_data["rating"] <= 5):
            filtered_data.pop("rating") 
        upd_data.update(filtered_data)
        db_request = "UPDATE quotes SET author=?, text=?, rating=? WHERE id=?"
        cursor.execute(db_request, (upd_data["author"], upd_data["text"], upd_data["rating"], upd_data["id"]))   
        connection.commit() 
        if cursor.rowcount:
            return upd_data, 200
        return {}, 418
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Фильтрованный список цитат
@app.route("/quotes/filter")
def filtered_quotes_list():
    cursor = get_db().cursor()
    args = request.args
    arg_author = args.get('author')
    arg_rating = args.get('rating')
    db_prefix = "SELECT * FROM quotes WHERE "
    if (arg_author is not None) and (arg_rating is not None):
        db_suffix = "author = ? AND rating = ?"
        db_args = (arg_author, arg_rating)
    elif (arg_author is not None) and (arg_rating is None):
        db_suffix = "author = ?"
        db_args = (arg_author,)
    elif (arg_author is None) and (arg_rating is not None):
        db_suffix = "rating = ?"
        db_args = (arg_rating,)
    else:
        return {}, 400
    db_request = db_prefix + db_suffix
    cursor.execute(db_request, db_args)
    quotes_db = cursor.fetchall()
    quotes = quotes_repack (quotes_db)
    return jsonify(quotes), 200

# Финальный обработчик
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

################################ Запуск ################################

if __name__ == "__main__":
    app.run(debug=True)