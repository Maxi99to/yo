from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модели
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    device = db.Column(db.String(100), nullable=False)
    problem = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Новая')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='requests')


# Создание БД
with app.app_context():
    db.create_all()

# HTML шаблон
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Сервис-центр</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; padding: 20px; background: #f0f2f5; }
        .container { max-width: 1200px; margin: auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .form-card, .requests-card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        input, textarea, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #007bff; color: white; }
        .status-new { background: #ffc107; padding: 5px 10px; border-radius: 5px; }
        .status-work { background: #17a2b8; color: white; padding: 5px 10px; border-radius: 5px; }
        .status-done { background: #28a745; color: white; padding: 5px 10px; border-radius: 5px; }
        .delete-btn { background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 5px; font-size: 12px; }
        .status-form { display: inline; margin-left: 10px; }
        .status-select { width: auto; display: inline; margin: 0 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Управление сервис-центром</h1>

        <div class="form-card">
            <h2>➕ Новая заявка</h2>
            <form method="POST" action="/add">
                <input type="text" name="client_name" placeholder="Имя клиента" required>
                <input type="text" name="client_phone" placeholder="Телефон" required>
                <input type="text" name="device" placeholder="Устройство (напр. iPhone 12)" required>
                <textarea name="problem" placeholder="Описание проблемы" rows="3" required></textarea>
                <button type="submit">Создать заявку</button>
            </form>
        </div>

        <div class="requests-card">
            <h2>📋 Все заявки</h2>
            <table>
                <thead>
                    <tr><th>ID</th><th>Клиент</th><th>Телефон</th><th>Устройство</th><th>Проблема</th><th>Статус</th><th>Действия</th></tr>
                </thead>
                <tbody>
                    {% for req in requests %}
                    <tr>
                        <td>{{ req.id }}</td>
                        <td>{{ req.client.name }}</td>
                        <td>{{ req.client.phone }}</td>
                        <td>{{ req.device }}</td>
                        <td>{{ req.problem[:50] }}{% if req.problem|length > 50 %}...{% endif %}</td>
                        <td>
                            <span class="
                                {% if req.status == 'Новая' %}status-new
                                {% elif req.status == 'В работе' %}status-work
                                {% elif req.status == 'Готово' %}status-done
                                {% endif %}
                            ">{{ req.status }}</span>

                            <form method="POST" action="/update_status/{{ req.id }}" class="status-form">
                                <select name="status" class="status-select">
                                    <option value="Новая" {% if req.status == 'Новая' %}selected{% endif %}>Новая</option>
                                    <option value="В работе" {% if req.status == 'В работе' %}selected{% endif %}>В работе</option>
                                    <option value="Готово" {% if req.status == 'Готово' %}selected{% endif %}>Готово</option>
                                </select>
                                <button type="submit" style="padding: 3px 8px; font-size: 12px;">✅</button>
                            </form>
                        </td>
                        <td>
                            <a href="/delete/{{ req.id }}" class="delete-btn" onclick="return confirm('Удалить заявку?')">Удалить</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    requests = Request.query.all()
    return render_template_string(HTML, requests=requests)


@app.route('/add', methods=['POST'])
def add():
    client = Client(
        name=request.form['client_name'],
        phone=request.form['client_phone']
    )
    db.session.add(client)
    db.session.flush()

    repair = Request(
        client_id=client.id,
        device=request.form['device'],
        problem=request.form['problem']
    )
    db.session.add(repair)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    req = Request.query.get_or_404(id)
    req.status = request.form['status']
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete(id):
    req = Request.query.get_or_404(id)
    db.session.delete(req)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)