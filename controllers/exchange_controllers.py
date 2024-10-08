from models.currency import Currency
from models.account import Account
from models.exchange import Exchange, exchange_schema, exchanges_schema
from init import db
from flask import Blueprint, request, jsonify

# Import the authorization decorator
from utils.authorization import check_account_user
# Import JWT-required decorator for authentication
from flask_jwt_extended import jwt_required

from sqlalchemy.exc import SQLAlchemyError  # Import SQLAlchemy error handling
# Import marshmallow validation error
from marshmallow.exceptions import ValidationError

# Create a blueprint for the exchange routes with a URL prefix that includes the account ID
exchange_bp = Blueprint("exchange", __name__, url_prefix="/<int:account_id>")


@exchange_bp.route("/exchange-history")
@jwt_required()  # Require JWT authentication for this route
@check_account_user  # Ensure the user has access to the account
def get_exchanges(account_id):
    """
    Retrieves the exchange history for a specific account_id.
    Ensures that the account belongs to the authenticated user.

    Parameters:
        account_id (int): The ID of the account for which to retrieve exchanges.

    Returns:
        JSON response containing the exchange history or a message if none exists.
    Raises:
        404: If no exchange history exists for the account.
        500: If there is a database operation failure.
    """

    try:
        # Retrieves all exchanges involving the specified account,
        # ordered by the date and time in descending order (most recent first).

        # SELECT *
        # FROM Exchange
        # WHERE from_account_id = (account_id) OR to_account_id = (account_id)
        # ORDER BY date_time DESC;
        statement = db.select(Exchange).filter(
            (Exchange.from_account_id == account_id) |  # OR opearator
            (Exchange.to_account_id == account_id)
        ).order_by(Exchange.date_time.desc())  # Order by date_time in descending order

        result = db.session.execute(statement)  # Execute the statement
        exchanges = result.scalars().all()  # Retrieve all exchange records

        if exchanges:
            # Return the exchanges in JSON format
            return jsonify(exchanges_schema.dump(exchanges))
        else:
            return {"message": f"There is NO exchanges operations history for the account {account_id}"}
    except SQLAlchemyError as e:
        return {"error": f"Database operation failed: {e}"}, 500


@exchange_bp.route("/transfer/<int:destination_id>", methods=["POST"])
@jwt_required()  # Require JWT authentication for this route
# Verify the account that initiates the transfer belongs to the current user
@check_account_user
def currency_exchange(account_id, destination_id):
    """
    Transfers funds from the source account to the destination account.
    The destination account can belong to any user. 
    If the source and destination accounts have different currency codes,
    the function converts the amount based on the current exchange rates.

    Parameters:
        account_id (int): The ID of the source account.
        destination_id (int): The ID of the destination account.

    Returns:
        JSON response containing the newly created exchange or an error message.
    Raises:
        400: If the transfer amount is invalid or if the input data is invalid.
        404: If the destination account does not exist.
        500: If there is a database operation failure.
    """

    # Check if the source and destination accounts are the same
    if account_id == destination_id:
        return {"error": "Cannot transfer funds to the same account. Please select a different account."}, 400

    # Load the request body and extract the amount
    body = exchange_schema.load(request.get_json())
    # Get the transfer amount from the request body
    amount = body.get("amount")
    if amount <= 0:
        return {"error": "Amount to transfer must be greater than 0"}, 400

    try:
        # Retrieves the source account to check the balance.

        # SELECT *
        # FROM Account
        # WHERE account_id = (account_id);
        statement = db.select(Account).filter_by(account_id=account_id)
        account_from = db.session.scalar(statement)

        # Check if the source account has sufficient funds
        if account_from.balance >= amount:
            # Deduct amount from source account
            account_from.balance = float(account_from.balance) - amount
        else:
            # Handle insufficient funds
            return {"error": f"Insufficient funds in the account {account_from.account_id}."}, 400

        # check if the two accounts have different currency_codes
        # if different currency_code, the currency conversion needs to be performed

        # SELECT *
        # FROM Account
        # WHERE account_id = (destination_id);
        statement = db.select(Account).filter_by(account_id=destination_id)
        account_to = db.session.scalar(statement)

        # if the destination account does NOT exist an error message is returned
        if not account_to:
            return {"error": f"The destination account ID {destination_id} does NOT exist"}, 404

        # Check if the two accounts have different currency codes
        if account_from.currency_code != account_to.currency_code:
            # Get the source currency

            # SELECT *
            # FROM Currency
            # WHERE currency_code = (currency_code);
            statement = db.select(Currency).filter_by(
                currency_code=account_from.currency_code)
            currency_from = db.session.scalar(statement)

            # Get the destination currency

            # SELECT *
            # FROM Currency
            # WHERE currency_code = (currency_code);
            statement = db.select(Currency).filter_by(
                currency_code=account_to.currency_code)
            currency_to = db.session.scalar(statement)

            # Convert the amount based on the current exchange rates
            amount_exchanged = (amount / currency_from.rate) * currency_to.rate
        else:
            # If the currency codes are the same, no conversion is needed
            amount_exchanged = amount

        # update the balance of the destination accont
        account_to.balance = float(account_to.balance) + amount_exchanged

        # Create a new instance of Exchange
        new_exchange = Exchange(
            amount=body.get("amount"),              # Original amount transferred
            amount_exchanged=amount_exchanged,      # Amount after conversion 
            description=body.get("description"),    # Description of the exchange
            account_origin=account_from,            # Reference to the source account
            account_destination=account_to          # Reference to the destination account
        )

        # Add the new exchange record to the session
        db.session.add(new_exchange)
        # Commit the transaction to the database
        db.session.commit()
        # Return the new exchange record
        return jsonify(exchange_schema.dump(new_exchange)), 201
    except ValidationError as ve:
        # Handle validation errors for the request data
        return {"error": f"Invalid input: {ve.messages}"}, 400
    except SQLAlchemyError as e:
        # Rollback the transaction in case of an error
        db.session.rollback()
        return {"error": f"Database operation failed {e}"}, 500
