import os
from flask import Flask,render_template
from flask_cors import CORS, cross_origin


# flask --app application run --debug

def create_app(test_config=None):
    # create and configure the ap
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    #allow CROS
    cors = CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    @app.route('/')
    def show_main_page():
        return render_template('base.html')
    
    @app.errorhandler(404)
    def not_found(error):
        return "<h2>Sorry, I'm afraid you are lost</h2>"

    from application.views import db
    db.init_app(app)

    from application.views import auth
    app.register_blueprint(auth.bp)

    from application.views import part
    app.register_blueprint(part.bp)

    from application.views import api
    app.register_blueprint(api.bp)


    return app