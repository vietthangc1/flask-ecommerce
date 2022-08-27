from datetime import datetime, date
from sys import prefix
import uuid
from flask import (
    Blueprint,
    flash, 
    redirect, 
    render_template, 
    url_for, 
    request, 
    session, 
    current_app,
    )

from dataclasses import asdict
from passlib.hash import pbkdf2_sha256
from slugify import slugify
from werkzeug.utils import secure_filename
import os

from ecom.forms import EditQuantityATCForm, LoginForm, PDPtoATCForm, RegisterForm
from .modules import get_num_cart_item, refresh_cate_tree, save_user_to_session
from bson.objectid import ObjectId
import locale
from .models import login_required
locale.setlocale(locale.LC_ALL, 'en_US')


pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)

@pages.route("/", methods = ["GET", "POST"])
def index():
    refresh_cate_tree()
    num_cart_item = get_num_cart_item()
    return render_template(
        "index.html",
        cate_tree = session.get("cate_tree"),
        num_cart_item = num_cart_item
        )

@pages.route("/category")
def category_listing(cate):
    refresh_cate_tree()
    list_product = [current_app.db.product.find({"cate_report": cate})]
    print([item["product_name"] for item in list_product])
    return render_template(
        "shop.html",
        cate_tree = session.get("cate_tree"),
        )

@pages.route("/sub_category/<string:cate>")
def sub_category_listing(cate):
    refresh_cate_tree()
    num_cart_item = get_num_cart_item()
    list_product = list(current_app.db.product.find({"sub_cate_report": cate}))

    return render_template(
        "shop.html",
        cate_tree = session.get("cate_tree"),
        list_product = list_product,
        num_cart_item = num_cart_item
        )

@pages.route("/product/<string:_id>", methods = ['GET','POST'])
def product_detail(_id):
    num_cart_item = get_num_cart_item()
    product = list(current_app.db.product.find({"_id": ObjectId(_id)}))[0]
    enu_imgs = enumerate(product.get("img_srcs"))
    product["description"] = product.get("description").replace("height", "")
    product["price_display"] = locale.format("%d", product["price"], grouping=True)    

    form = PDPtoATCForm()

    if form.validate_on_submit():
        dic = dict(
            product_id = _id,
            quantity = form.quantity.data
        )

        current_user = session.get("current_user")
        lst_cart = current_user["cart_items"]

        lst_product_id_in_cart = [item["product_id"] for item in lst_cart]
        if _id not in lst_product_id_in_cart:
            lst_cart.append(dic)
        else:
            for product in lst_cart:
                if product["product_id"] == _id:
                    product["quantity"] += dic["quantity"]

        current_app.db.users.update_one({"email": session.get("email")}, {"$set": {"cart_items": lst_cart}})
        save_user_to_session()
        print("added ",dic["quantity"])
        return redirect(request.path)

    return render_template(
        "detail.html",
        product = product,
        enu_imgs = enu_imgs,
        num_cart_item = num_cart_item,
        form = form
    )

@pages.route("/cart", methods = ['GET', 'POST'])
@login_required
def cart():
    lst_cart = session.get("current_user").get("cart_items")
    num_cart_item = len(lst_cart)
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
    
    for i in range(len(lst_cart)):
        product = lst_cart[i]
        product["product_name"] = product_dictionary[ObjectId(product["product_id"])]["product_name"]
        product["price"] = product_dictionary[ObjectId(product["product_id"])]["price"]
        product["img_src"] = product_dictionary[ObjectId(product["product_id"])]["img_src"]
        
        form = EditQuantityATCForm(prefix=product["product_id"])
        form.quantity.default = product["quantity"]
        form.process()
        product["form"] = form

    if request.method == "POST":
        push_list = []        
        data = request.form
        for k in data.keys():
            if ("quantity" in k):
                v = int(data.get(k))
                if (v > 0):
                    product_id = k.split("-")[0]
                    quantity = v
                    push_list.append({
                        "product_id": product_id,
                        "quantity": quantity
                    })
        current_app.db.users.update_one(
            {
                "email": session.get("email")
            },
            {
                "$set": {
                    "cart_items": push_list
                }
            }
        )
        save_user_to_session()

        return redirect(url_for("pages.cart"))

    
    return render_template(
        "cart.html",
        list_product = lst_cart,
        num_cart_item = num_cart_item
        )

@pages.route("/checkout")
@login_required
def checkout():
    lst_cart = session.get("current_user").get("cart_items")
    num_cart_item = len(lst_cart)
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
    
    for i in range(len(lst_cart)):
        product = lst_cart[i]
        product["product_name"] = product_dictionary[ObjectId(product["product_id"])]["product_name"]
        product["price"] = product_dictionary[ObjectId(product["product_id"])]["price"]
        product["img_src"] = product_dictionary[ObjectId(product["product_id"])]["img_src"]
        product["total_value"] = product["price"] * product["quantity"]

    total_order_value = sum([product["total_value"] for product in lst_cart])

    return render_template(
        "checkout.html",
        list_product = lst_cart,
        num_cart_item = num_cart_item,
        total_order_value = total_order_value
    )

@pages.route("/order")
@login_required
def order():
    lst_cart = session.get("current_user").get("cart_items")
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
    
    for i in range(len(lst_cart)):
        product = lst_cart[i]
        product["product_name"] = product_dictionary[ObjectId(product["product_id"])]["product_name"]
        product["price"] = product_dictionary[ObjectId(product["product_id"])]["price"]
        product["img_src"] = product_dictionary[ObjectId(product["product_id"])]["img_src"]
        product["total_value"] = product["price"] * product["quantity"]

    total_order_value = sum([product["total_value"] for product in lst_cart])

    order_id = uuid.uuid4().hex
    current_app.db.orders.insert_one({
        "_id": order_id,
        "items": lst_cart,
        "value": total_order_value
    })

    current_app.db.users.update_one({"email": session.get("email")}, {"$push": {"orders": order_id}})
    current_app.db.users.update_one({"email": session.get("email")}, {"$set": {"cart_items": []}})
    save_user_to_session()

    return render_template(
        "orders.html",
        num_cart_item = 0,
    )

@pages.route("/register", methods = ['GET','POST'])
def register():
    if session.get("email"):
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        user = dict(
            _id = uuid.uuid4().hex,
            email = form.email.data,
            password = pbkdf2_sha256.hash(form.password.data),
            cart_items = [],
            orders = []
        )
        lst_email = [u['email'] for u in list(current_app.db.users.find({}, {"email": 1}))]
        if user["email"] in lst_email:
            flash("This email had been registerd already. Use another email!", "danger")
            return redirect("/register")
        current_app.db.users.insert_one(user)
        flash("Registered Successfully!", "success")
        return redirect("/login")
    return render_template('register.html', th_form = form, title="Register")


@pages.route("/login", methods = ['GET','POST'])
def login():
    if session.get("email"):
        if session.get("url_bf_login") != None:
            url = session.get("url_bf_login")
            session["url_bf_login"] = None
            return redirect(url)
        return redirect("/")

    form = LoginForm()

    if form.validate_on_submit():
        login_dic = {
            'email' : form.email.data,
            'password': form.password.data
        }
        user = list(current_app.db.users.find({"email": login_dic['email']}))
        if len(user) > 0:
            if pbkdf2_sha256.verify(login_dic['password'], user[0]['password']):
                session['email'] = login_dic['email']
                save_user_to_session()
                return redirect(request.path)
        flash("Wrong email or password!", "danger")
    return render_template('login.html', th_form = form, title="Log in")

@pages.route("/logout")
def logout():
    session['email'] = None
    session['current_user'] = None
    return redirect("/")