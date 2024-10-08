from models.currency import Currency, currencies_schema

from init import db
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

# Create a Blueprint for currency routes
currency_bp = Blueprint("currencies", __name__, url_prefix="/currencies")


@currency_bp.route("/")
@jwt_required()         # Ensure the user is authenticated
def get_all_currencies():
    """
    Retrieves all currency records from the database, 
    ensuring that the data is sorted by currency code.

    Returns:
        JSON response containing a list of all currencies.
    Raises:
        500: If there is a database operation failure.
    """

    try:
        # Create a query to retrieve all currencies from the database, ordered by the currency code.

        # SELECT *
        # FROM Currency
        # ORDER BY currency_code;

        statement = db.select(Currency).order_by(Currency.currency_code)
        accounts = db.session.scalars(statement)

        # Serialize the data and return as JSON
        return jsonify(currencies_schema.dump(accounts))
    except SQLAlchemyError as e:
        return {"error": f"Database operation failed: {e}"}, 500
