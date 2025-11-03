from __future__ import annotations

from datetime import datetime

from app import db


class Wine(db.Model):
    __tablename__ = "wines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    producer = db.Column(db.String(120))
    region = db.Column(db.String(120))
    grapes = db.Column(db.String(120))
    year = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bottles = db.relationship("Bottle", back_populates="wine", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Wine {self.name!r}>"

    @property
    def total_quantity(self) -> int:
        return sum(bottle.quantity for bottle in self.bottles)

    @property
    def estimated_value(self) -> float:
        return sum((bottle.price or 0) * bottle.quantity for bottle in self.bottles)


class Bottle(db.Model):
    __tablename__ = "bottles"

    id = db.Column(db.Integer, primary_key=True)
    wine_id = db.Column(db.Integer, db.ForeignKey("wines.id"), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)
    storage_location = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wine = db.relationship("Wine", back_populates="bottles")

    def __repr__(self) -> str:
        return f"<Bottle {self.id} of {self.wine.name!r}>"
