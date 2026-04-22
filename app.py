import random
import datetime
from flask import Flask, request, jsonify, g
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func
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

class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    surname: Mapped[str] = mapped_column(String(32), nullable=True, default=None) 
    deleted: Mapped[bool] = mapped_column(nullable=False, default=False)  
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic')

    def __init__(self, name, surname=None):
        self.name = name
        self.surname = surname
        self.deleted = False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "deleted": self.deleted
        }

class QuoteModel(db.Model):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(nullable=False, default=1)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())  
    deleted: Mapped[bool] = mapped_column(nullable=False, default=False)  

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text = text
        self.rating = rating
        self.deleted = False

    def to_dict(self):
        # Форматируем дату в "dd.mm.yyyy"
        date_str = self.created.strftime("%d.%m.%Y") if self.created else ""
        
        return {
            "id": self.id,
            "text": self.text,
            "rating": self.rating,
            "author_name": self.author.name,
            "author_surname": self.author.surname,
            "created": date_str,
            "deleted": self.deleted
        }

################################ Обработчики ################################
     
###################### Авторы ######################
# Получить список авторов
# @app.route("/authors")
# def authors_list():
#     authors_db = db.session.query(AuthorModel).filter(AuthorModel.deleted == False).all()
#     authors = []
#     for author in authors_db:
#         authors.append(author.to_dict())
#     return jsonify(authors), 200

# Получить список авторов с сортировкой
@app.route("/authors")
def authors_list():
    query = db.session.query(AuthorModel).filter(AuthorModel.deleted == False)
    orderby = request.args.get('orderby')
    asc = request.args.get('asc', 'true').lower() == 'true'  # по умолчанию True
    if orderby == 'name':
        if asc:
            query = query.order_by(AuthorModel.name.asc())
        else:
            query = query.order_by(AuthorModel.name.desc())
    elif orderby == 'surname':
        if asc:
            query = query.order_by(AuthorModel.surname.asc())
        else:
            query = query.order_by(AuthorModel.surname.desc())
    elif orderby == 'fullname':
        if asc:
            query = query.order_by(AuthorModel.surname.asc(), AuthorModel.name.asc())
        else:
            query = query.order_by(AuthorModel.surname.desc(), AuthorModel.name.desc())
    else:
        if asc:
            query = query.order_by(AuthorModel.id.asc())
        else:
            query = query.order_by(AuthorModel.id.desc())
    authors_db = query.all()
    authors = [author.to_dict() for author in authors_db]
    return jsonify(authors), 200

# Получить список всех удалённых авторов
@app.route("/alldeletedauthors")
def all_deleted_authors():
    authors_db = db.session.query(AuthorModel).filter(AuthorModel.deleted == True).all()
    authors = [author.to_dict() for author in authors_db]
    return jsonify(authors), 200

# Получить автора по id
@app.route("/authors/<int:author_id>")
def author_get_by_id(author_id: int):
    author = db.session.query(AuthorModel).filter(
        AuthorModel.id == author_id,
        AuthorModel.deleted == False
    ).first()
    if author:
        return jsonify(author.to_dict()), 200
    return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404   

# Создание автора
@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    if not author_data.get("name"):
        return jsonify({"Ошибка": "Поле 'name' обязательно для заполнения"}), 400
    author = AuthorModel(name=author_data["name"])
    if "surname" in author_data:
        author.surname = author_data["surname"]
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201

# Изменяем существующего автора
@app.route("/authors/<int:author_id>", methods=['PUT'])
def edit_author(author_id: int):
    author = db.session.query(AuthorModel).filter(
        AuthorModel.id == author_id,
        AuthorModel.deleted == False
    ).first()
    if author:
        new_data = request.json
        if "name" in new_data:
            author.name = new_data["name"]
        if "surname" in new_data:
            author.surname = new_data["surname"]
        db.session.commit()
        return jsonify(author.to_dict()), 200
    return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404

# "Удаляем" автора и его цитаты
@app.route("/authors/<int:author_id>", methods=['DELETE'])
def delete_author(author_id: int):
    author = db.session.query(AuthorModel).filter(
        AuthorModel.id == author_id,
        AuthorModel.deleted == False
    ).first()
    if author:
        author.deleted = True
        db.session.query(QuoteModel).filter_by(author_id=author_id).update({"deleted": True})
        db.session.commit()
        return jsonify({"message": f"Автор '{author_id}' и все его цитаты помечены как удалённые"}), 200    
    return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404

# Восстанавливаем всех удалённых авторов и их цитаты
@app.route("/restorealldeletedauthors", methods=['PUT'])
def restore_all_deleted_authors():
    deleted_authors = db.session.query(AuthorModel).filter(AuthorModel.deleted == True).all()
    if not deleted_authors:
        return jsonify({
            "message": "Нет удалённых авторов для восстановления",
            "restored_authors_count": 0,
            "restored_quotes_count": 0
        }), 200
    restored_authors = []
    restored_quotes_count = 0
    for author in deleted_authors:
        author.deleted = False
        restored_authors.append(f"{author.name} {author.surname or ''}".strip())
        quotes_count = db.session.query(QuoteModel).filter(
            QuoteModel.author_id == author.id,
            QuoteModel.deleted == True
        ).update({"deleted": False})
        restored_quotes_count += quotes_count
    db.session.commit()
    return jsonify({
        "message": f"Восстановлено {len(restored_authors)} авторов и {restored_quotes_count} цитат",
        "restored_authors": restored_authors,
        "restored_authors_count": len(restored_authors),
        "restored_quotes_count": restored_quotes_count
    }), 200    

###################### Цитаты ######################
# Полный список цитат
@app.route("/quotes/")
def quotes_list():
    quotes_db = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).all()
    quotes = [quote.to_dict() for quote in quotes_db]
    return jsonify(quotes), 200

# Пересчитываем наличные цитаты
@app.route("/quotes/count")
def quotes_count():
    count = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).count()
    return jsonify({"count": count}), 200

# Цитируем случайно
@app.route("/quotes/random")
def quotes_rnd():
    random_quote = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).order_by(db.func.random()).first()
    if random_quote:
        return jsonify(random_quote.to_dict()), 200
    return jsonify({"Ошибка": "Мешок с цитатами пуст"}), 404

# Выдаём цитату по id
@app.route("/quotes/<int:quote_id>")
def quote_get_by_id(quote_id):
    quote = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.id == quote_id,
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).first()
    if quote:
        return jsonify(quote.to_dict()), 200
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Получаем все цитаты автора 
@app.route("/authors/<int:author_id>/quotes", methods=["GET"])
def get_author_quotes(author_id: int):
    author = db.session.query(AuthorModel).filter(
        AuthorModel.id == author_id,
        AuthorModel.deleted == False
    ).first()
    if not author:
        return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404
    quotes = db.session.query(QuoteModel).filter(
        QuoteModel.author_id == author_id,
        QuoteModel.deleted == False
    ).all()
    return jsonify([quote.to_dict() for quote in quotes]), 200    

# "Удаляем" указанную цитату
@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
    quote = db.session.query(QuoteModel).filter(
        QuoteModel.id == quote_id,
        QuoteModel.deleted == False
    ).first()
    if quote:
        quote.deleted = True
        db.session.commit()
        return jsonify({"message": f"Цитата с id={quote_id} удалена."}), 200
    return jsonify({"message": f"Цитата с id={quote_id} не найдена."}), 404

# Добавляем цитату автору с указанным id
@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_authors_quote(author_id: int):
    author = db.session.query(AuthorModel).filter(
        AuthorModel.id == author_id,
        AuthorModel.deleted == False
    ).first()
    if not author:
        return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404
    new_quote = request.json
    rating = new_quote.get("rating", 1)
    if rating < 1 or rating > 5:
        rating = 1
    q = QuoteModel(author, new_quote["text"], rating)
    db.session.add(q)
    db.session.commit()
    return jsonify(q.to_dict()), 201
    
# Изменяем существующую цитату
@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    quote = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.id == quote_id,
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).first()
    if quote:
        new_data = request.json
        if "text" in new_data:
            quote.text = new_data["text"]
        if "rating" in new_data and 1 <= new_data["rating"] <= 5:
            quote.rating = new_data["rating"]
        db.session.commit()
        return jsonify(quote.to_dict()), 200
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Изменяем рейтинг цитаты 
@app.route("/quotes/<int:quote_id>/rating", methods=['PUT'])
def change_quote_rating(quote_id):
    direction = request.args.get('set')
    if direction not in ['up', 'down']:
        return jsonify({"Ошибка": "Параметр 'set' должен быть 'up' или 'down'"}), 400
    quote = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.id == quote_id,
        QuoteModel.deleted == False,
        AuthorModel.deleted == False
    ).first()
    if quote:
        if direction == 'up' and quote.rating < 5:
            quote.rating += 1
        elif direction == 'down' and quote.rating > 1:
            quote.rating -= 1
        db.session.commit()
        return jsonify(quote.to_dict()), 200    
    return jsonify({"Ошибка": f"Цитата с id={quote_id} не найдена"}), 404

# Восстановить все удалённые цитаты у неудалённых авторов
@app.route("/restorealldeletedquotes", methods=['PUT'])
def restore_all_deleted_quotes():
    deleted_quotes = db.session.query(QuoteModel).join(AuthorModel).filter(
        QuoteModel.deleted == True,
        AuthorModel.deleted == False
    ).all()
    if not deleted_quotes:
        return jsonify({"message": "Нет удалённых цитат для восстановления"}), 200
    restored_quotes_num = 0
    for quote in deleted_quotes:
        quote.deleted = False
        restored_quotes_num += 1
    db.session.commit()
    return jsonify({"message": f"Восстановлено {restored_quotes_num} цитат"}), 200    

################################ Запуск ################################

if __name__ == "__main__":
    app.run(debug=True)