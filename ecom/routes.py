from datetime import datetime, date
from nis import cat
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

from ecom.forms import AddProductForm, EditProductForm, EditQuantityATCForm, LoginForm, PDPtoATCForm, RegisterForm
from .modules import add_to_cart, get_current_time, get_product_dictionary, update_information
import locale
from .models import Product, login_required
locale.setlocale(locale.LC_ALL, 'en_US')


pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)


@pages.route("/", methods=["GET", "POST"])
def index():
    meta = update_information()
    return render_template(
        "index.html",
        cate_tree=meta.get("cate_tree"),
        num_cart_item=meta['num_cart_item']
    )


@pages.route("/category")
def category_listing(cate):
    meta = update_information()
    list_product = [current_app.db.product.find({"cate_report": cate})]
    print([item["product_name"] for item in list_product])
    return render_template(
        "shop.html",
        cate_tree=meta.get("cate_tree"),
    )


@pages.route("/sub_category/<string:cate>", methods=['GET', 'POST'])
def sub_category_listing(cate):
    meta = update_information()
    list_product = list(current_app.db.product.find({
        "sub_cate_report": cate,
        "stocks": {"$gt": 0}}))

    if request.method == "POST":
        if session.get("email") == None:
            return redirect(url_for('pages.login'))

        _id = str(request.form.get("btn"))
        product_dictionary = get_product_dictionary(_id)

        current_user = meta["current_user"]
        lst_cart = current_user["cart_items"]

        quantity = 1
        add_to_cart(_id, quantity, lst_cart, product_dictionary)

        return redirect(request.path)

    return render_template(
        "shop.html",
        cate_tree=meta.get("cate_tree"),
        list_product=list_product,
        num_cart_item=meta["num_cart_item"]
    )


@pages.route("/product/<string:_id>", methods=['GET', 'POST'])
def product_detail(_id):
    meta = update_information()
    product = list(current_app.db.product.find({"_id": _id}))[0]
    enu_imgs = enumerate(product.get("img_srcs"))
    product["description"] = product.get("description").replace("height", "")
    product["price_display"] = locale.format(
        "%d", product["price"], grouping=True)

    form = PDPtoATCForm()

    if form.validate_on_submit():
        if session.get("email") == None:
            return redirect(url_for('pages.login'))

        product_dictionary = get_product_dictionary(_id)

        current_user = meta["current_user"]
        lst_cart = current_user["cart_items"]
        quantity = form.quantity.data

        add_to_cart(_id, quantity, lst_cart, product_dictionary)
        return redirect(request.path)

    return render_template(
        "detail.html",
        product=product,
        enu_imgs=enu_imgs,
        num_cart_item=meta["num_cart_item"],
        form=form
    )


@pages.route("/cart", methods=['GET', 'POST'])
@login_required
def cart():
    meta = update_information()
    lst_cart = meta["current_user"].get("cart_items")

    for i in range(len(lst_cart)):
        product = lst_cart[i]

        form = EditQuantityATCForm(prefix=product["product_id"])
        form.quantity.default = product["quantity"]
        form.process()
        product["form"] = form

    if request.method == "POST":
        data = request.form

        current_app.db.users.update_one(
            {
                "email": session.get("email")
            },
            {
                "$set": {
                    "cart_items": []
                }
            }
        )

        for k in data.keys():
            if ("quantity" in k):
                v = int(data.get(k))
                if (v > 0):
                    product_id = k.split("-")[0]
                    product_dictionary = get_product_dictionary(product_id)
                    meta = update_information()
                    lst_cart = meta["current_user"].get("cart_items")
                    quantity = v
                    add_to_cart(product_id, quantity,
                                lst_cart, product_dictionary)

        return redirect(url_for("pages.cart"))

    return render_template(
        "cart.html",
        list_product=lst_cart,
        num_cart_item=meta["num_cart_item"]
    )


@pages.route("/checkout")
@login_required
def checkout():
    meta = update_information()
    lst_cart = meta["current_user"].get("cart_items")

    for i in range(len(lst_cart)):
        product = lst_cart[i]
        product["total_value"] = product["price"] * product["quantity"]
        product["total_value_display"] = locale.format(
            "%d", product["total_value"], grouping=True)

    total_order_value = sum([product["total_value"] for product in lst_cart])
    total_order_value_display = locale.format(
        "%d", total_order_value, grouping=True)

    return render_template(
        "checkout.html",
        list_product=lst_cart,
        num_cart_item=meta["num_cart_item"],
        total_order_value=total_order_value_display
    )


@pages.route("/order_success")
@login_required
def order():
    meta = update_information()
    lst_cart = meta["current_user"].get("cart_items")
    if len(lst_cart) == 0:
        return redirect(url_for('pages.index'))

    for i in range(len(lst_cart)):
        product = lst_cart[i]
        product["total_value"] = product["price"] * product["quantity"]

    total_order_value = sum([product["total_value"] for product in lst_cart])

    order_id = uuid.uuid4().hex
    current_app.db.orders.insert_one({
        "_id": order_id,
        "items": lst_cart,
        "value": total_order_value,
        "order_time": get_current_time(),
        "customer_email": session.get("email")
    })

    for item in lst_cart:
        product_id = item["product_id"]
        quantity = item["quantity"]
        print("{} - {}".format(product_id, quantity))
        current_app.db.product.update_one(
            {"_id": product_id},
            {"$inc": {
                "stocks": -quantity,
                "sales": quantity
            }
            })

    current_app.db.users.update_one({"email": session.get("email")}, {
                                    "$push": {"orders": order_id}})
    current_app.db.users.update_one({"email": session.get("email")}, {
                                    "$set": {"cart_items": []}})

    return render_template(
        "orders.html",
        num_cart_item=0,
    )


@pages.route("/orders")
@login_required
def orders_listing():
    meta = update_information()
    lst_cart = meta["current_user"].get("cart_items")

    product_dictionary = {}
    lst_order_id = meta["current_user"].get("orders")
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

    orders = list(current_app.db.orders.find({"_id": {"$in": lst_order_id}}))

    return render_template(
        "orders_listing.html",
        num_cart_item=len(lst_cart),
        orders=orders
    )


@pages.route("/login", methods=['GET', 'POST'])
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
            'email': form.email.data,
            'password': form.password.data
        }
        user = list(current_app.db.users.find({"email": login_dic['email']}))
        if len(user) > 0:
            if pbkdf2_sha256.verify(login_dic['password'], user[0]['password']):
                session['email'] = login_dic['email']
                return redirect(request.path)
        flash("Wrong email or password!", "danger")
    return render_template('login.html', th_form=form, title="Log in")


@pages.route("/logout")
def logout():
    session['email'] = None
    session['current_user'] = None
    return redirect("/")

# Seller Center


@pages.route("/seller", methods=['GET'])
def seller_index():
    return render_template("seller_index.html")


@pages.route("/seller/add_products", methods=['GET', 'POST'])
@login_required
def seller_add_products():
    form = AddProductForm()

    if form.validate_on_submit():
        f = form.img_file.data
        if f == None:
            img_src = ''
        else:
            img_path = os.path.dirname(os.path.realpath(
                __file__))+"/static/img/product_img/"
            img_src = uuid.uuid4().hex + "." + f.filename.split(".")[-1]
            f.save(img_path+img_src)

        product_info = dict(
            _id=uuid.uuid4().hex,
            product_name=form.product_name.data,
            cate_report=form.cate_report.data,
            sub_cate_report=form.sub_cate_report.data,
            brand=form.brand.data,
            price=form.price.data,
            stocks=form.stocks.data,
            img_srcs=[img_src],
            listed=form.listed.data,
            description=request.form.get("description"),
            sales=0,
            seller=session.get("email")
        )

        current_app.db.product.insert_one(product_info)
        return redirect(url_for('pages.seller_index'))
    return render_template(
        "seller_add_products.html",
        title="Add products",
        th_form=form
    )


@pages.route("/seller/stocks", methods=['GET', 'POST'])
@login_required
def seller_stocks():
    list_products = list(current_app.db.product.find(
        {"seller": session.get("email")}))
    return render_template(
        "seller_stocks.html",
        title="Stocks management",
        list_products=list_products)


@pages.route("/seller/toggle_listed/<string:_id>", methods=['GET', 'POST'])
@login_required
def seller_toggle_listed(_id):
    product_info = list(current_app.db.product.find({"_id": _id}))[0]
    if product_info["seller"] != session.get("email"):
        return redirect(url_for('pages.seller_stocks'))
    if product_info["listed"] == 0:
        current_app.db.product.update_one(
            {"_id": _id}, {"$set": {"listed": 1}})
    else:
        current_app.db.product.update_one(
            {"_id": _id}, {"$set": {"listed": 0}})
    return redirect(url_for('pages.seller_stocks'))


@pages.route("/seller/remove_confirmation/<string:_id>", methods=['GET', 'POST'])
@login_required
def seller_remove_confirmation(_id):
    product_info = list(current_app.db.product.find({"_id": _id}))[0]
    if product_info["seller"] != session.get("email"):
        return redirect(url_for('pages.seller_stocks'))
    return render_template(
        "seller_remove_confirmation.html",
        title="Delete Confirmation",
        product=product_info)


@pages.route("/seller/remove/<string:_id>", methods=['GET', 'POST'])
@login_required
def seller_remove(_id):
    product_info = list(current_app.db.product.find({"_id": _id}))[0]
    if product_info["seller"] != session.get("email"):
        return redirect(url_for('pages.seller_stocks'))
    print(_id)
    current_app.db.product.delete_one({"_id": _id})
    return redirect(url_for('pages.seller_stocks'))


@pages.route("/seller/edit/<string:_id>", methods=['GET', 'POST'])
@login_required
def seller_edit_products(_id):
    product_info = list(current_app.db.product.find({"_id": _id}))[0]
    if product_info["seller"] != session.get("email"):
        return redirect(url_for('pages.seller_stocks'))
    product = Product(**product_info)

    form = EditProductForm(obj=product)

    if form.validate_on_submit():
        f = form.img_file.data
        current_img_srcs = product_info["img_srcs"]
        if f != None:
            img_path = os.path.dirname(os.path.realpath(
                __file__))+"/static/img/product_img/"
            img_src = uuid.uuid4().hex + "." + f.filename.split(".")[-1]
            f.save(img_path+img_src)
            if current_img_srcs != None:
                current_img_srcs.append(img_src)
            else:
                current_img_srcs = [img_src]

        edited_product_info = dict(
            _id=product_info["_id"],
            product_name=product_info["product_name"],
            cate_report=product_info["cate_report"],
            sub_cate_report=product_info["sub_cate_report"],
            brand=form.brand.data,
            price=int(form.price.data),
            seller=product_info["seller"],
            stocks=int(form.stocks.data),
            img_srcs=current_img_srcs,
            listed=int(form.listed.data),
            description=request.form.get("description"),
            sales=product_info["sales"]
        )
        current_app.db.product.update_one(
            {"_id": _id}, {"$set": edited_product_info})
        return redirect(url_for('pages.seller_stocks'))

    return render_template(
        "seller_edit_products.html",
        title="Edit product",
        th_form=form,
        product_info=product_info
    )


@pages.route("/seller/delete_img/<string:img_src>/<string:_id>", methods=['GET', 'POST'])
@login_required
def seller_delete_product_img(img_src, _id):
    product_info = list(current_app.db.product.find({"_id": _id}))[0]
    if product_info["seller"] != session.get("email"):
        return redirect(url_for('pages.seller_stocks'))
    current_app.db.product.update_one(
        {"_id": _id}, {"$pull": {"img_srcs": img_src}})
    img_path = os.path.dirname(os.path.realpath(
        __file__))+"/static/img/product_img/"
    os.remove(img_path+img_src)
    return redirect(url_for('pages.seller_edit_products', _id=_id))


@pages.route("/seller/login", methods=['GET', 'POST'])
def seller_login():
    if session.get("email"):
        if session.get("url_bf_login") != None:
            url = session.get("url_bf_login")
            session["url_bf_login"] = None
            return redirect(url)
        return redirect(url_for('pages.seller_index'))

    form = LoginForm()

    if form.validate_on_submit():
        login_dic = {
            'email': form.email.data,
            'password': form.password.data
        }
        user = list(current_app.db.users.find({"email": login_dic['email']}))
        if len(user) > 0:
            if pbkdf2_sha256.verify(login_dic['password'], user[0]['password']):
                session['email'] = login_dic['email']
                return redirect(request.path)
        flash("Wrong email or password!", "danger")
    return render_template("seller_login.html", th_form=form, title="Log in")


@pages.route("/seller/logout")
def seller_logout():
    session['email'] = None
    session['current_user'] = None
    return redirect(url_for('pages.seller_index'))


@pages.route("/register", methods=['GET', 'POST'])
def register():
    if session.get("email"):
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        user = dict(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
            cart_items=[],
            orders=[]
        )
        lst_email = [u['email']
                     for u in list(current_app.db.users.find({}, {"email": 1}))]
        if user["email"] in lst_email:
            flash("This email had been registerd already. Use another email!", "danger")
            return redirect("/register")
        current_app.db.users.insert_one(user)
        flash("Registered Successfully!", "success")
        return redirect("/login")
    return render_template('register.html', th_form=form, title="Register")
