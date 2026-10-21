# database.py — Khởi tạo DB và seed sản phẩm & tài khoản admin khi kết nối DB mới

from models import db, Product, User

INITIAL_PRODUCTS = [
    {
        "name": "Acc Free Fire Lv20 Mail7day",
        "price": 15000,
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&h=400&fit=crop",
        "description": "Acc Free Fire Level 20, via Mail 7 ngay. Giao hang ngay sau khi thanh toan.",
        "stock": 0
    },
    {
        "name": "Acc Free Fire Lv20 Gmail",
        "price": 20000,
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&h=400&fit=crop",
        "description": "Acc Free Fire Level 20, via Gmail chinh chu. Bao doi trong 24h.",
        "stock": 0
    }
]

def seed_products():
    """Khởi tạo sản phẩm và tài khoản admin ban đầu nếu database còn trống."""
    try:
        # 1. Khởi tạo sản phẩm nếu chưa có
        if Product.query.count() == 0:
            for p in INITIAL_PRODUCTS:
                prod = Product(**p)
                db.session.add(prod)
            db.session.commit()
            print("[DB] Da tao san pham mac dinh.")

        # 2. Khởi tạo tài khoản admin nếu chưa có
        if not User.query.filter_by(username='ddonline77').first():
            u1 = User(
                username='ddonline77',
                password_hash='scrypt:32768:8:1$tKnEpZzI8BsSfamo$86dc6986c9a3a1f11c663326a1c1455173bf58360c1ec2b88f9a4451e07b930e50e4f679c5b14af8d61cb6eb1ee8512e7d31d1365b8be665e2f723825112aa72',
                balance=2670000.0,
                is_admin=True
            )
            db.session.add(u1)

        if not User.query.filter_by(username='Minh123').first():
            u2 = User(
                username='Minh123',
                password_hash='scrypt:32768:8:1$w19OPuCunHoa2W8e$7cccdbc6c4d97b790be02aa8755a47941d97ecb9ff73493abf90e943963ff77ca4e5ec16cb320ae81fc01d75047b196181e9e396b3c7f2951599e935513b1bc1',
                balance=20000.0,
                is_admin=True
            )
            db.session.add(u2)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[DB INIT ERROR] {e}")
