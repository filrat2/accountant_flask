# -*- coding: utf-8 -*-

# import needed modules
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic
from datetime import datetime

# database config
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
db_store = SQLAlchemy(app)


# define database tables as classes
class Product(db_store.Model):
    id = db_store.Column(db_store.Integer, primary_key=True)
    name = db_store.Column(db_store.String(50), unique=True,
                           nullable=False)
    price = db_store.Column(db_store.Integer, unique=False,
                            nullable=False)
    count = db_store.Column(db_store.Integer, unique=False,
                            nullable=False)


class Account(db_store.Model):
    id = db_store.Column(db_store.Integer, primary_key=True)
    balance = db_store.Column(db_store.Integer, unique=False,
                              nullable=False)


class Record(db_store.Model):
    id = db_store.Column(db_store.Integer, primary_key=True)
    message = db_store.Column(db_store.String(250), unique=False,
                              nullable=False)
    date = db_store.Column(db_store.String(17), unique=False,
                           nullable=False)


# function for create record in history
def create_history_record(message):
    date = datetime.now()
    record = Record(message=message,
                    date=date.strftime("%d-%m-%Y, %H:%M"))
    db_store.session.add(record)
    db_store.session.commit()


# create database
with app.app_context():
    db_store.create_all()

# define account balance and save it in database (in Account table)
ACCOUNT_ID = 1
with app.app_context():
    if not Account.query.filter_by(id=ACCOUNT_ID).first():
        account = Account(id=ACCOUNT_ID, balance=5000)

        db_store.session.add(account)
        db_store.session.commit()


# define endpoints
@app.route("/", methods=['GET', 'POST'])
def main():
    account = Account.query.filter_by(id=ACCOUNT_ID).first()
    products = Product.query.all()
    return render_template('main.html', account=account, products=products)


@app.route("/history", methods=['GET', 'POST'])
def history():
    start_id = request.form.get('start_id')
    end_id = request.form.get('end_id')

    if start_id is None or start_id == "":
        start_id = ""
    else:
        start_id = int(start_id)

    if end_id is None or end_id == "":
        end_id = ""
    else:
        end_id = int(end_id)

    if start_id == "" or end_id == "":
        history = Record.query.all()
    elif start_id <= 0 or end_id <= 0:
        history = Record.query.all()
    else:
        history = db_store.session.query(Record).filter(
            Record.id.between(start_id, end_id))
    return render_template('history.html', history=history)


@app.route("/sell", methods=['GET', 'POST'])
def sell():
    if request.method == "POST":
        item_name = request.form.get('product_name')
        item_count = request.form.get('product_count')

        message = f"<a href='{url_for('main')}'>Powrót do strony głównej</a>"

        errors = []

        if item_name == "":
            errors.append("Identyfikator produktu nie może być pusty!")

        if item_count == "" or int(item_count) <= 0:
            errors.append("Liczba kupowanych produktów musi być większa od 0!")
        else:
            item_count = int(item_count)

        if errors:
            errors.append(message)
            return "</br></br>".join(errors), 400

        product = Product.query.filter_by(name=item_name).first()

        account = Account.query.filter_by(id=ACCOUNT_ID).first()

        if not account:
            pass

        if product and product.count == 0:
            message_fail = (f"Niewystarczająca ilość produktu {item_name}."
                            " Sprzedaż towaru nie może zastać zrealizowana.")
            create_history_record(message_fail)

            return (f"Artykuł <i>'{product.name}'</i> aktualnie niedostępny."
                    "</br>Sprzedaż towaru nie może zostać zrealizowana."
                    "</br></br>" + message, 400)

        elif product:
            if product.count >= item_count:
                product.count -= item_count
                total_price = item_count * product.price
                account.balance += total_price

                message_sell = (f"Sprzedano {item_count} sztuk produktu "
                                f"{item_name}, którego cena za sztukę wynosi "
                                f"{product.price}. Całkowita "
                                f"kwota sprzedaży wynosi {total_price}.")

                create_history_record(message_sell)
                db_store.session.commit()
            else:
                msg_fail = (f"Niewystarczająca ilość produktu {item_name}."
                            " Sprzedaż towaru nie może zastać zrealizowana.")
                create_history_record(msg_fail)
                return (f"Niewystarczająca ilość produktu {product.name}.</br>"
                        "Sprzedaż towaru nie może zostać zrealizowana.</br>"
                        f"</br>Na stanie znajduje się tylko {product.count}  "
                        f"sztuk produktu {product.name}.</br>Podaj inną liczbę"
                        " sprzedawanych sztuk.</br></br>" + message, 400)

        else:
            return (f"Brak artykułu o nazwie <i>'{item_name}'</i>.</br>"
                    "Sprzedaż towaru nie może zostać zrealizowana."
                    "</br></br>" + message, 400)

        return redirect(url_for('main'))


@app.route('/buy', methods=["GET", "POST"])
def buy():
    if request.method == "POST":
        item_name = request.form.get('product_name')
        item_price = request.form.get('product_price')
        item_count = request.form.get('product_count')

        message = f"<a href='{url_for('main')}'>Powrót do strony głównej</a>"

        errors = []

        if item_name == "":
            errors.append("Identyfikator produktu nie może być pusty!")

        if item_price == "" or float(item_price) <= 0:
            errors.append("Cena produktu musi być większa od 0!")
        else:
            item_price = float(item_price)

        if item_count == "" or int(item_count) <= 0:
            errors.append("Liczba kupowanych produktów musi być większa od 0!")
        else:
            item_count = int(item_count)

        if errors:
            errors.append(message)
            return "</br></br>".join(errors), 400

        product = Product.query.filter_by(name=item_name).first()

        total_price = item_price * item_count
        message_buy = (f"Zakupiono {item_count} sztuk produktu "
                       f"{item_name}, którego cena za sztukę wynosi "
                       f"{item_price}. "
                       f"Całkowita kwota zakupu wynosi {total_price}.")
        message_fail = ("Niewystarczające środki na koncie. Zakup towaru nie "
                        "może być zrealziowany.")

        account = Account.query.filter_by(id=ACCOUNT_ID).first()

        if not account:
            pass

        elif total_price > account.balance:
            create_history_record(message_fail)
            return ("Niewystarczające środki na koncie.</br>Zakup towaru nie "
                    "może być zrealziowany.</br>Posiadasz za mało środków na "
                    f"koncie na zakup takiej ilości towaru za {total_price}."
                    f"</br>Twoje saldo wynosi {account.balance}.</br></br>"
                    + message, 400)

        if product:
            create_history_record(message_buy)
            product.price = item_price
            product.count += item_count

            db_store.session.commit()
        else:
            create_history_record(message_buy)
            product = Product(name=item_name,
                              price=item_price,
                              count=item_count)

            db_store.session.add(product)
            db_store.session.commit()

        account.balance -= total_price
        db_store.session.commit()

        return redirect(url_for('main'))


@app.route("/acc_change", methods=['GET', 'POST'])
def account_balance_change():
    if request.method == "POST":
        balance_change = request.form.get('value')
        comment = request.form.get('comment')
        account = Account.query.filter_by(id=ACCOUNT_ID).first()

        message = f"<a href='{url_for('main')}'>Powrót do strony głównej</a>"

        if balance_change == "" or float(balance_change) == 0:
            return ("Zmiana konta musi być różna od 0!</br></br>"
                    + message, 400)
        else:
            deposit_money = (f"Wpłata kwoty {balance_change} "
                             "na konto zakończona powodzeniem. "
                             f"Poprzedni stan konta: {account.balance}."
                             f" Komentarz do operacji: {comment}")

            withdraw_money = (f"Wypłata kwoty {abs(float(balance_change))} "
                              "z konta zakończona powodzeniem. Poprzedni stan "
                              f"konta {account.balance}. Komentarz do operacji"
                              f": {comment}")

            balance_change = float(balance_change)
            if (account.balance + balance_change) > 0:
                account.balance += balance_change

                db_store.session.commit()

                if balance_change > 0:
                    create_history_record(deposit_money)
                else:
                    create_history_record(withdraw_money)

            else:
                fail = ("Wypłata środków zakończona niepowodzeniem. "
                        "Posiadasz za mało środków na koncie na "
                        f"wypłacenie kwoty {abs(float(balance_change))}. "
                        f"Twoje saldo wynosi {account.balance}.")
                create_history_record(fail)
                return ("Posiadasz za mało środków na koncie na wypłacenie "
                        "takiej kwoty.</br></br>Wypłata środków zakończona "
                        "niepowodzeniem.</br>Posiadasz za mało środków na "
                        f"koncie na wypłacenie kwoty {abs(balance_change)}."
                        f"</br>Twoje saldo wynosi {account.balance}.</br></br>"
                        + message, 400)

        return redirect(url_for('main'))


alembic = Alembic()
alembic.init_app(app)
