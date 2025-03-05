from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1111@localhost:5433/KR'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)

# Модели базы данных
class Classifier(db.Model):
    __tablename__ = 'classifier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('classifier.id'))


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50))
    main_volume = db.Column(db.Float)


class Defect(db.Model):
    __tablename__ = 'defect'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    status = db.Column(db.String(50))
    date_detected = db.Column(db.Date)
    description = db.Column(db.Text)


# Список всех таблиц
TABLES = {
    'classifier': Classifier,
    'item': Item,
    'defect': Defect
}


# Главная страница
@app.route('/')
def index():
    return render_template('index.html', tables=TABLES.keys())


@app.template_filter('dynamic_getattr')
def jinja_getattr(obj, attr):
    return getattr(obj, attr, None)


# Управление таблицей и объединениями
@app.route('/table/<string:table_name>', methods=['GET', 'POST'])
def manage_table(table_name):
    model = TABLES.get(table_name)
    if not model:
        return f"Table {table_name} not found.", 404

    # Проверка на выбор связанных таблиц
    join_table = request.args.get('join')
    items = None

    if join_table and join_table in TABLES:
        join_model = TABLES[join_table]

        # Пример JOIN: Item -> Defect
        if table_name == 'item' and join_table == 'defect':
            items = db.session.query(Item, Defect).join(Defect, Item.id == Defect.item_id).all()
        # Пример JOIN: Defect -> Item
        elif table_name == 'defect' and join_table == 'item':
            items = db.session.query(Defect, Item).join(Item, Defect.item_id == Item.id).all()
        else:
            return f"Join between {table_name} and {join_table} is not supported.", 400
    else:
        items = model.query.all()

    # Добавление нового элемента
    if request.method == 'POST':
        new_data = {key: request.form[key] for key in request.form if hasattr(model, key)}
        new_entry = model(**new_data)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('manage_table', table_name=table_name))

    return render_template(
        'table.html',
        table_name=table_name.capitalize(),
        items=items,
        fields=model.__table__.columns.keys(),
        join_table=join_table
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
