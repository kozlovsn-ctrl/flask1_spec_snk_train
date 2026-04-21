import sqlite3

create_quotes = """
INSERT INTO
quotes (author,text)
VALUES
('Rick Cook', 'Программирование сегодня — это гонка разработчиков программ...'),
('Waldi Ravens', 'Программирование на С похоже на быстрые танцы на только...');
"""

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


# Подключение в БД
connection = sqlite3.connect("store.db")

# Создаем cursor, он позволяет делать SQL-запросы
cursor = connection.cursor()

for quote in quotes:
    create_quote = "INSERT INTO quotes (author,text,rating) VALUES (?, ?, ?)"
    cursor.execute(create_quote, (quote["author"], quote["text"], quote["rating"]))
    connection.commit()

# Выполняем запрос:
# cursor.execute(create_quotes)

# Фиксируем выполнение(транзакцию)
connection.commit()

# Закрыть курсор:
cursor.close()

# Закрыть соединение:
connection.close()
