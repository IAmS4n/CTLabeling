import os

from flask import Flask, url_for, redirect


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=os.path.join(app.instance_path, "ct.sqlite"))

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object("config.Config")
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db

    db.init_app(app)

    from . import auth
    from . import panel

    app.register_blueprint(auth.bp)
    app.register_blueprint(panel.bp)

    @app.route("/")
    def root():
        return redirect(url_for("panel.show_list"))

    return app
