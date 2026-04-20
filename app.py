from flask import Flask

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

@app.route("/quotes")
def quotes_list():
    return quotes


if __name__ == "__main__":
    app.run(debug=True)