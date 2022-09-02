from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from flask import (
    redirect, 
    session, 
    current_app,
    request
    )
import functools
from flask import (
  current_app
)

@dataclass
class Product:
    _id: str
    product_name: str
    cate_report: str
    sub_cate_report: str
    brand: str
    price: int
    seller: str
    description: str
    stocks: int
    sales: int
    listed: int
    img_srcs: List[str] = field(default_factory=list)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        _email = session.get("email")
        lst_user = list(current_app.db.users.find({}))
        lst_email = [user['email'] for user in lst_user]
        if _email not in lst_email:
            session['url_bf_login'] = request.path
            return redirect("/login")
        return route(*args, **kwargs)
    return route_wrapper