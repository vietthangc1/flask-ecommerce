from flask import current_app, session
from datetime import date, datetime
import pytz
import json

def save_user_to_session():
  	session['current_user'] = list(current_app.db.users.find({"email": session.get("email")}))[0]

def get_num_cart_item():
    if session.get("email") == None:
        num_cart_item = 0
    else:
        user = list(current_app.db.users.find({"email": session.get("email")}))[0]
        cart = user.get("cart_items")
        if cart == None:
            num_cart_item = 0
        else:
            num_cart_item = len(cart)    
    return num_cart_item

def get_current_time():
    return datetime.now(tz=pytz.timezone('Asia/Bangkok'))

def update_information():
    with open("ecom/static/data/cate_tree.json", "r", encoding='utf-8') as f:
        cate_tree = json.load(f)

    if session.get("email") == None:
        num_cart_item = 0
        current_user = {}
    else:
        current_user = list(current_app.db.users.find({"email": session.get("email")}))[0]
        cart = current_user.get("cart_items")
        if cart == None:
            num_cart_item = 0
        else:
            num_cart_item = len(cart)  

    return {
        'current_user': current_user,
        'num_cart_item': num_cart_item,
        'cate_tree': cate_tree
    }

def get_product_dictionary():
    product_dictionary = {}
    list_products = list(current_app.db.product.find({}))
    for product in list_products:
        img = product.get("img_srcs")
        if len(img) == 0:
            img = ""
        else:
            img = product.get("img_srcs")[0]
        product_dictionary[product["_id"]] = {
            "product_name": product["product_name"],
            "price": product["price"],
            "img_src": img
        }
    return product_dictionary