import os

from flask import Flask, render_template

from config import Config
from models import db
from routes.fatura_routes import fatura_bp
from routes.odeme_routes import odeme_bp
from routes.eslestirme_routes import eslestirme_bp
from routes.musteri_routes import musteri_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(fatura_bp)
    app.register_blueprint(odeme_bp)
    app.register_blueprint(eslestirme_bp)
    app.register_blueprint(musteri_bp)

    @app.route("/")
    def anasayfa():
        return render_template("index.html")

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
