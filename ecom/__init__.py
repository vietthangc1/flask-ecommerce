import os
from flask import Flask
from dotenv import load_dotenv
from pymongo import MongoClient
import urllib
from ecom.routes import pages
from flask_qrcode import QRcode

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["MONGODB_URI"] = "mongodb+srv://vietthangc1:"+urllib.parse.quote_plus('f2bdx@*-uLAZz!f')+"@cluster0.le7ea.mongodb.net/test"
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "pf9Wkote4IKEAXvy-cQkrDohv9Cb3Ag-wyJILbq_dFw"
    )
    app.db = MongoClient(app.config["MONGODB_URI"])["ecom"]
    QRcode(app)
    app.register_blueprint(pages)
    return app
