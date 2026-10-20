# models.py — Định nghĩa các bảng cơ sở dữ liệu (SQLAlchemy ORM)

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """Bảng người dùng: lưu thông tin đăng ký, mật khẩu đã hash và số dư."""
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    balance     = db.Column(db.Float, default=0.0)          # Số dư tài khoản (VNĐ)
    is_admin    = db.Column(db.Boolean, default=False)      # Quyền quản trị viên
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    orders      = db.relationship('Order', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)


class Product(db.Model):
    """Bảng sản phẩm: thông tin hàng hóa trong cửa hàng."""
    __tablename__ = 'products'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    price       = db.Column(db.Float, nullable=False)
    image_url   = db.Column(db.String(500))
    description = db.Column(db.Text)
    stock       = db.Column(db.Integer, default=0)


class Order(db.Model):
    """Bảng đơn hàng: ghi lại mỗi lần mua hàng thành công."""
    __tablename__ = 'orders'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status       = db.Column(db.String(20), default='success')  # success / cancelled
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    items        = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    """Chi tiết từng sản phẩm trong một đơn hàng."""
    __tablename__ = 'order_items'
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    product    = db.relationship('Product')


class Transaction(db.Model):
    """Bảng giao dịch nạp tiền: lưu mã QR và trạng thái chờ / thành công."""
    __tablename__ = 'transactions'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount     = db.Column(db.Float, nullable=False)
    trans_code = db.Column(db.String(30), unique=True, nullable=False)   # NAP{user_id}_{rand4}
    status     = db.Column(db.String(10), default='pending')             # pending / success
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GameAccount(db.Model):
    """Kho tài khoản game thực tế (tk|mk) được admin nạp vào cho từng sản phẩm."""
    __tablename__ = 'game_accounts'
    id           = db.Column(db.Integer, primary_key=True)
    product_id   = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    account_info = db.Column(db.Text, nullable=False)            # Dạng tk|mk hoặc thông tin chi tiết
    status       = db.Column(db.String(20), default='available') # 'available' (còn hàng) hoặc 'sold' (đã bán)
    order_id     = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True) # ID đơn hàng khi đã bán
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    sold_at      = db.Column(db.DateTime, nullable=True)

    product      = db.relationship('Product', backref=db.backref('game_accounts', lazy=True, cascade='all, delete-orphan'))
    order        = db.relationship('Order', backref=db.backref('delivered_accounts', lazy=True))

