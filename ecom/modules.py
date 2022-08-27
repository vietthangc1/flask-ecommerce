from flask import current_app, session
from datetime import date, datetime
import pytz

def refresh_cate_tree():
  if session.get("cate_tree") == None:
    raw_cate = list(current_app.db.product.aggregate( 
            [
                {"$group": { "_id": {
                    "cate_report": "$cate_report", 
                    "sub_cate_report": "$sub_cate_report" } } }
            ]
        ))
    cate_tree = {}
    for item in raw_cate:
        print(item)
        cate = item["_id"]["cate_report"]
        sub_cate = item["_id"]["sub_cate_report"]
        if cate not in cate_tree:
            cate_tree[cate] = [sub_cate]
        else:
            cate_tree[cate].append(sub_cate)
    session["cate_tree"] = cate_tree

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
        'num_cart_item': num_cart_item
    }