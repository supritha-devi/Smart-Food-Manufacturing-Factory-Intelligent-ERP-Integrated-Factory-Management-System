from flask import Blueprint

voice_bp = Blueprint("voice", __name__, url_prefix="/voice")

from app.voice import routes
