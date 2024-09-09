from init import db, ma
from marshmallow import fields
from sqlalchemy import func

class Exchange(db.Model):
    __tablename__ = "exchanges"
    exchange_id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    description = db.Column(db.String)
    date = db.Column(db.DateTime, default=func.now())

    from_account_id = db.Column(db.Integer, db.ForeignKey("accounts.account_id"), nullable=False)
    # to_account_id = db.Column(db.Integer, db.ForeignKey("accounts.account_id"), nullable=False)

    sender_account = db.relationship("Account", foreign_keys=[from_account_id], back_populates="sender_exchange")
    # destination_account = db.relationship("Account", foreign_keys=[to_account_id], back_populates="exchanges_to")

class ExchangeSchema(ma.Schema):
    sender_account = fields.Nested("AccountSChema")
    destination_account = fields.Nested("AccountSChema")
    class Meta:
        fields = ("exchange_id", "amount", "curency", "description", "date", "sender_account", "destination_account")
