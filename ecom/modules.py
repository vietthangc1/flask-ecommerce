from flask import current_app, session
from datetime import date, datetime
import pytz
import json
import locale
locale.setlocale(locale.LC_ALL, 'en_US')

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

def get_product_dictionary(_id):
    product_dictionary = {}
    list_products = list(current_app.db.product.find({"_id": _id}))
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

def add_to_cart(_id, quantity, lst_cart, product_dictionary):
    lst_product_id_in_cart = [item["product_id"] for item in lst_cart]
    if _id not in lst_product_id_in_cart:
        dic = dict(
            product_id = _id,
            quantity = quantity,
            product_name = product_dictionary[_id]["product_name"],
            price = product_dictionary[_id]["price"],
            img_src =product_dictionary[_id]["img_src"],
            price_display = locale.format("%d", product_dictionary[_id]["price"], grouping=True)    
        )
        lst_cart.append(dic)

    else:
        for product in lst_cart:
            if product["product_id"] == _id:
                product["quantity"] += quantity

    current_app.db.users.update_one({"email": session.get("email")}, {"$set": {"cart_items": lst_cart}})