from flask import Blueprint, Flask


def create_app(blueprint: Blueprint) -> Flask:
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    return app
