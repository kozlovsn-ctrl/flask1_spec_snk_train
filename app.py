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
@app.route("/authors")
def authors_list():
    authors_db = db.session.scalars(db.select(AuthorModel)).all()
    authors = []
    for author in authors_db:
        authors.append(author.to_dict())
    return jsonify(authors), 200

# Получить автора по id
@app.route("/authors/<int:author_id>")
def author_get_by_id(author_id: int):
    author = db.session.get(AuthorModel, author_id)
    if author:
        return jsonify(author.to_dict()), 200
    return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404    

# Создание автора
@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    author = AuthorModel(author_data["name"])
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201  

# Изменяем существующего автора
@app.route("/authors/<int:author_id>", methods=['PUT'])
def edit_author(author_id: int):
    author = db.session.get(AuthorModel, author_id)
    if author:
        new_data = request.json
        if "name" in new_data:
            author.name = new_data["name"]
            db.session.commit()
        return jsonify(author.to_dict()), 200    
    return jsonify({"Ошибка": f"Автор с id={author_id} не найден"}), 404


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_authors_quote(author_id: int):
    author = db.session.get(AuthorModel, author_id)
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

###################### Цитаты ######################
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

###################### Нужно один раз ######################

# Добавление тестовых данных
@app.route("/db/fillitcomplete", methods=['GET'])
def fill_database():
    try:
        test_data = {
            "Альберт": {
                "surname": "Эйнштейн",
                "quotes": [
                    ("Жизнь - как езда на велосипеде. Чтобы сохранить равновесие, ты должен двигаться.", 5),
                    ("Воображение важнее знаний.", 5),
                    ("Бесконечны только Вселенная и человеческая глупость, причём насчёт Вселенной я не уверен.", 4)
                ]
            },
            "Кон": {
                "surname": "Фуций",
                "quotes": [
                    ("Выберите работу по душе, и вам не придётся работать ни одного дня в своей жизни.", 5),
                    ("Настоящая доброта проистекает из сердца. Никогда не оставляй в своём сердце места для злобы.", 4),
                    ("Неважно, как медленно ты идёшь, главное - не останавливаться.", 5)
                ]
            },
            "Оскар": {
                "surname": "Уайльд",
                "quotes": [
                    ("Будь собой, прочие роли уже заняты.", 5),
                    ("Я всегда с огромным удовольствием узнаю, что меня в чём-то не устраивает - значит, я не такой, как все.", 4),
                    ("Лучший способ избавиться от искушения - поддаться ему.", 3)
                ]
            },
            "Лев": {
                    "surname": "Толстой",
                    "quotes": [
                        ("Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему.", 5),
                        ("Нет величия там, где нет простоты, добра и правды.", 5),
                        ("Знание без нравственной основы — ничего не значит.", 4)
                    ]
                },
                "Фёдор": {
                    "surname": "Достоевский",
                    "quotes": [
                        ("Красота спасёт мир.", 5),
                        ("Надо любить жизнь больше, чем смысл жизни.", 4),
                        ("Человек есть тайна. Её надо разгадывать, и ежели будешь её разгадывать всю жизнь, то не говори, что потерял время.", 5)
                    ]
                },
                "Антон": {
                    "surname": "Чехов",
                    "quotes": [
                        ("Краткость — сестра таланта.", 5),
                        ("В человеке должно быть всё прекрасно: и лицо, и одежда, и душа, и мысли.", 5),
                        ("Если человек здоров, значит, у него есть надежда, а если у него есть надежда, значит, у него есть всё.", 4)
                    ]
                }
        }
        
        created_authors = []
        created_quotes = []
        
        for author_name, author_data in test_data.items():
            # Проверяем, существует ли уже автор (не удалённый)
            existing_author = db.session.query(AuthorModel).filter(
                AuthorModel.name == author_name,
                AuthorModel.deleted == False
            ).first()
            
            if existing_author:
                author = existing_author
                created_authors.append(f"{author_name} (уже существовал)")
            else:
                author = AuthorModel(
                    name=author_name,
                    surname=author_data["surname"]
                )
                db.session.add(author)
                db.session.flush()
                created_authors.append(f"{author_name} {author_data['surname']}")
            
            # Добавляем цитаты для автора
            for quote_text, rating in author_data["quotes"]:
                existing_quote = db.session.query(QuoteModel).filter_by(
                    author_id=author.id,
                    text=quote_text,
                    deleted=False
                ).first()
                
                if not existing_quote:
                    quote = QuoteModel(
                        author=author,
                        text=quote_text,
                        rating=rating
                    )
                    db.session.add(quote)
                    created_quotes.append(f"'{quote_text[:30]}...' - {author_name} (рейтинг: {rating})")
        
        db.session.commit()
        
        return jsonify({
            "message": "База данных успешно заполнена тестовыми данными",
            "added_authors": created_authors,
            "added_quotes_count": len(created_quotes),
            "quotes_sample": created_quotes[:5] + ["..."] if len(created_quotes) > 5 else created_quotes
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Ошибка при заполнении базы данных",
            "details": str(e)
        }), 500

################################ Запуск ################################

if __name__ == "__main__":
    app.run(debug=True)