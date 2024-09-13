from flask import current_app
from flask import Blueprint
from init import db, bcrypt
from models.user import User
from models.account import Account
from models.deposit import Deposit
from models.exchange import Exchange
from models.currency import Currency
from datetime import datetime
from utils.currency_rates import update_currency


db_commands = Blueprint("db", __name__)


@db_commands.cli.command("create")
def create_tables():
    db.create_all()
    print("Tables created!")

@db_commands.cli.command("drop")
def drop_tables():
        # Connect to the database
        with current_app.app_context():
            db.reflect()  # Reflect the current database structure
            db.drop_all()  # This will drop all tables
            print("All tables dropped successfully")

@db_commands.cli.command("seed")
def seed_database():
    
    users = [
        User(
            name="danilo",
            email="danilo.lann@gmail.com",
            password=bcrypt.generate_password_hash("123456").decode('utf8'),
            is_admin=True
        ),

        User(
            name="User 2",
            email="alberto@gmail.com",
            password=bcrypt.generate_password_hash("5678").decode('utf8'),
            is_admin=True
        ),

        User(
            name="User 3",
            email="marco@gmail.com",
            password=bcrypt.generate_password_hash("10998765").decode('utf8')
        )
    ]
    
    accounts = [
        Account(
            currency_code = "AUD",
            balance = 1000,
            date_creation = datetime.now(),
            user = users[0]
        ),
            Account(
            currency_code = "EUR",
            balance = 3500.76,
            date_creation = datetime.now(),
            user = users[0]
        ),
            Account(
            currency_code = "USD",
            balance = 597,
            date_creation = datetime.now(),
            user = users[1]
        ),
            Account(
            currency_code = "USD",
            balance = 300,
            date_creation = datetime.now(),
            user = users[2]
        )
    ]

    deposits = [
        Deposit(
            currency_code = "EUR",
            amount = 200,
            description = "Savings",
            date_time = datetime.now(),
            account = accounts[1]
        ),
        Deposit(
            currency_code = "USD",
            amount = 1050,
            description = "car",
            date_time = datetime.now(),
            account = accounts[2]
        ),
        Deposit(
            currency_code = "AUD",
            amount = 200,
            description = "Savings",
            date_time = datetime.now(),
            account = accounts[0]
        ),
        Deposit(
            currency_code = "EUR",
            amount = 200,
            description = "Savings",
            date_time = datetime.now(),
            account = accounts[1]
        )
    ]

    

    update_currency()

    db.session.add_all(deposits)
    db.session.add_all(users)
    print("Users added succesfully")
    db.session.add_all(accounts)
    print("Accounts added succesfully")
    
    try:
        db.session.commit()
        print("Tables seeded!")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
