from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'winecellar.db')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from models import Bottle, Wine

    @app.before_first_request
    def create_tables() -> None:
        db.create_all()

    @app.context_processor
    def inject_now() -> dict[str, datetime]:
        return {"now": datetime.utcnow()}

    @app.route("/")
    def dashboard() -> str:
        wines = Wine.query.order_by(Wine.name).all()
        total_bottles = sum(bottle.quantity for bottle in Bottle.query.all())
        total_value = sum(bottle.quantity * (bottle.price or 0) for bottle in Bottle.query.all())
        return render_template(
            "dashboard.html",
            wines=wines,
            total_bottles=total_bottles,
            total_value=total_value,
        )

    @app.route("/wines")
    def list_wines() -> str:
        wines = Wine.query.order_by(Wine.name).all()
        return render_template("wines/list.html", wines=wines)

    @app.route("/wines/new", methods=["GET", "POST"])
    def create_wine() -> str:
        if request.method == "POST":
            wine = Wine(
                name=request.form["name"].strip(),
                producer=request.form.get("producer", "").strip() or None,
                region=request.form.get("region", "").strip() or None,
                grapes=request.form.get("grapes", "").strip() or None,
                year=int(request.form["year"]) if request.form.get("year") else None,
                notes=request.form.get("notes", "").strip() or None,
            )
            db.session.add(wine)
            db.session.commit()
            flash("Вино успешно добавлено", "success")
            return redirect(url_for("list_wines"))
        return render_template("wines/form.html", wine=None)

    @app.route("/wines/<int:wine_id>")
    def view_wine(wine_id: int) -> str:
        wine = Wine.query.get_or_404(wine_id)
        return render_template("wines/detail.html", wine=wine)

    @app.route("/wines/<int:wine_id>/edit", methods=["GET", "POST"])
    def edit_wine(wine_id: int) -> str:
        wine = Wine.query.get_or_404(wine_id)
        if request.method == "POST":
            wine.name = request.form["name"].strip()
            wine.producer = request.form.get("producer", "").strip() or None
            wine.region = request.form.get("region", "").strip() or None
            wine.grapes = request.form.get("grapes", "").strip() or None
            wine.year = int(request.form["year"]) if request.form.get("year") else None
            wine.notes = request.form.get("notes", "").strip() or None
            db.session.commit()
            flash("Информация о вине обновлена", "success")
            return redirect(url_for("view_wine", wine_id=wine.id))
        return render_template("wines/form.html", wine=wine)

    @app.route("/wines/<int:wine_id>/delete", methods=["POST"])
    def delete_wine(wine_id: int) -> str:
        wine = Wine.query.get_or_404(wine_id)
        db.session.delete(wine)
        db.session.commit()
        flash("Вино удалено", "info")
        return redirect(url_for("list_wines"))

    @app.route("/bottles/new", methods=["POST"])
    def create_bottle() -> str:
        wine_id = int(request.form["wine_id"])
        wine = Wine.query.get_or_404(wine_id)
        bottle = Bottle(
            wine_id=wine.id,
            purchase_date=datetime.strptime(request.form["purchase_date"], "%Y-%m-%d"),
            quantity=int(request.form.get("quantity", 1)),
            price=float(request.form["price"]) if request.form.get("price") else None,
            storage_location=request.form.get("storage_location", "").strip() or None,
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(bottle)
        db.session.commit()
        flash("Бутылка добавлена", "success")
        return redirect(url_for("view_wine", wine_id=wine.id))

    @app.route("/bottles/<int:bottle_id>/delete", methods=["POST"])
    def delete_bottle(bottle_id: int) -> str:
        bottle = Bottle.query.get_or_404(bottle_id)
        wine_id = bottle.wine_id
        db.session.delete(bottle)
        db.session.commit()
        flash("Запись о бутылке удалена", "info")
        return redirect(url_for("view_wine", wine_id=wine_id))

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
