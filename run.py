from flask import Flask

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)

    from app import blueprint
    app.register_blueprint(blueprint, url_prefix='/api')

    return app

if __name__ == "__main__":
    app = create_app('config')
    app.run(debug=True)