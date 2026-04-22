import random
from flask import Flask, request, jsonify, g
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from flask_migrate import Migrate
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    pass

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)

# Добавил столбец с рейтингом в существующую базу (в консоли с контекстом):
# with db.engine.connect() as conn:
#     conn.execute(db.text('ALTER TABLE quotes ADD COLUMN rating INTEGER DEFAULT 1 NOT NULL'))
#     conn.commit()

class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
    quotes: Mapped[list['QuoteModel']] = relationship( back_populates='author', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            "name": self.text,
        }

class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))

    def __init__(self, author, text):
        self.author = author
        self.text  = text

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text
        }

################################ Обработчики ################################

#Создание автора
@app.route("/authors", methods=["POST"])
def create_author():
       author_data = request.json
       author = AuthorModel(author_data["name"])
       db.session.add(author)
       db.session.commit()
       return author.to_dict(), 201

@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id: int):
   author = db.session.get(author_id)
   new_quote = request.json
   q = QuoteModel(author, new_quote["text"])
   db.session.add(q)
   db.session.commit()
   return q.to_dict(), 201

# Полный список цитат
@app.route("/quotes/")
def quotes_list():
    quotes_db = db.session.scalars(db.select(QuoteModel)).all()
    quotes = []
    for quote in quotes_db:
        quotes.append(quote.to_dict())
    # print (quotes)
    return jsonify(quotes), 200

# Пересчитываем наличные цитаты
@app.route("/quotes/count")
def quotes_count():
    count = db.session.query(QuoteModel).count()
    return jsonify({"count": count}), 200

# Цитируем случайно
@app.route("/quotes/random")
def quotes_rnd():
    random_quote = db.session.query(QuoteModel).order_by(db.func.random()).first()
    if random_quote:
        return jsonify(random_quote.to_dict()), 200
    return jsonify({"Ошибка": "Мешок с цитатами пуст"}), 404

# Выдаём цитату по id
@app.route("/quotes/<int:quote_id>")
def quote_get_by_id(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if quote:
        return jsonify(quote.to_dict()), 200
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Удаляем указанную цитату
@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
    deleted = db.session.query(QuoteModel).filter_by(id=quote_id).delete()
    db.session.commit()
    if deleted:
        return jsonify({"message": f"Цитата с id={quote_id} удалена."}), 200
    return jsonify({"message": f"Цитата с id={quote_id} не найдена."}), 404

# Вносим новую цитату
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    if "rating" in data and 1 <= data["rating"] <= 5:
        rating = data["rating"]
    else:
        rating = None  # База сама проставит 1 по умолчанию
    new_quote = QuoteModel(
        author=data["author"],
        text=data["text"],
        rating=rating
    )
    db.session.add(new_quote)
    db.session.commit()
    return jsonify(new_quote.to_dict()), 201
    
# Изменяем существующую цитату
@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if quote:
        upd_data = quote.to_dict()
        new_data = request.json
        if "author" in new_data:
            quote.author = new_data["author"]
        if "text" in new_data:
            quote.text = new_data["text"]
        if "rating" in new_data and 1 <= new_data["rating"] <= 5:
            quote.rating = new_data["rating"]
        db.session.commit()
        return jsonify(quote.to_dict()), 200
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Фильтрованный список цитат
@app.route("/quotes/filter")
def filtered_quotes_list():
    args = request.args
    arg_author = args.get('author')
    arg_rating = args.get('rating')
    query = db.select(QuoteModel)
    if arg_author is not None and arg_rating is not None:
        query = query.where(QuoteModel.author == arg_author, QuoteModel.rating == int(arg_rating))
    elif arg_author is not None:
        query = query.where(QuoteModel.author == arg_author)
    elif arg_rating is not None:
        query = query.where(QuoteModel.rating == int(arg_rating))
    else:
        return jsonify({}), 400
    quotes_db = db.session.scalars(query).all()
    quotes = [quote.to_dict() for quote in quotes_db]
    return jsonify(quotes), 200

################################ Запуск ################################

if __name__ == "__main__":
    app.run(debug=True)