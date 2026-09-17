from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.musteri import Musteri  # noqa: E402,F401
from models.hesap_plani import HesapPlani  # noqa: E402,F401
from models.fatura import Fatura  # noqa: E402,F401
from models.odeme import Odeme  # noqa: E402,F401
from models.eslestirme import Eslestirme  # noqa: E402,F401
