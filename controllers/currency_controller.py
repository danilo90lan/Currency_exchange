from models.currency import Currency, currencies_schema

from init import db
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

currency_bp = Blueprint("currencies", __name__, url_prefix="/currencies")

@currency_bp.route("/")
@jwt_required()
def get_all_currencies():
    try: 
        statement = db.select(Currency).order_by(Currency.currency_code)
        accounts = db.session.scalars(statement)
        return jsonify(currencies_schema.dump(accounts))
    except SQLAlchemyError as e:
        return {"error": f"Database operation failed: {e}"}, 500 