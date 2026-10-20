# app.py — Flask application chính: routes, API, xử lý business logic

import os
import random
import string
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Product, Order, OrderItem, Transaction, GameAccount
from database import seed_products

# ─────────────────────────────────────────────────────────────────────────────
# Khởi tạo Flask app
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'shopkey-change-in-production-2024')

# Cấu hình SQLite — file shop.db nằm cạnh app.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "shop.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Tạo bảng và seed dữ liệu mẫu khi khởi động lần đầu
with app.app_context():
    db.create_all()
    seed_products()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Decorator yêu cầu đăng nhập
# ─────────────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # Nếu là AJAX request (Content-Type JSON hoặc XMLHttpRequest)
            # → trả về JSON 401 thay vì redirect HTML (tránh lỗi res.json() parse thất bại)
            is_ajax = (request.is_json or
                       request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                       request.path.startswith('/api/'))
            if is_ajax:
                return jsonify({'success': False, 'message': 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.'}), 401
            flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator kiểm tra quyền Admin: chỉ user có is_admin=True mới được truy cập."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập tài khoản quản trị.', 'warning')
            return redirect(url_for('login'))
        user = get_current_user()
        if not user or not user.is_admin:
            flash('Bạn không có quyền truy cập trang quản trị!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def format_vnd(amount):
    """Định dạng số tiền thành chuỗi VNĐ, ví dụ: 1.500.000đ"""
    return f"{int(amount):,}đ".replace(',', '.')


def get_current_user():
    """Lấy đối tượng User hiện tại từ session."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Context processor: inject user vào tất cả templates
# ─────────────────────────────────────────────────────────────────────────────
@app.context_processor
def inject_user():
    user = get_current_user()
    return {
        'current_user': user,
        'format_vnd': format_vnd,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES: Xác thực (Authentication)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản mới."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Kiểm tra đầu vào
        if not username or not password:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Tên đăng nhập phải có ít nhất 3 ký tự.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Mật khẩu xác nhận không khớp.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.', 'error')
            return render_template('register.html')

        # Tạo user mới với mật khẩu đã được hash
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw, balance=0.0)
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập bằng username + password."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        # Kiểm tra user tồn tại và mật khẩu đúng
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Chào mừng trở lại, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Đăng xuất và xóa session."""
    session.clear()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('index'))


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES: Trang chủ & Sản phẩm
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Trang chủ: hiển thị danh sách sản phẩm với tìm kiếm và lọc giá."""
    query    = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    products = Product.query

    # Lọc theo từ khóa tìm kiếm (case-insensitive)
    if query:
        products = products.filter(Product.name.ilike(f'%{query}%'))

    # Lọc theo khoảng giá
    if min_price is not None:
        products = products.filter(Product.price >= min_price)
    if max_price is not None:
        products = products.filter(Product.price <= max_price)

    products = products.all()

    return render_template('index.html',
                           products=products,
                           query=query,
                           min_price=min_price,
                           max_price=max_price)


@app.route('/orders')
@login_required
def orders():
    """Trang lịch sử đơn hàng của người dùng đã đăng nhập."""
    user = get_current_user()
    user_orders = (Order.query
                   .filter_by(user_id=user.id)
                   .order_by(Order.created_at.desc())
                   .all())
    return render_template('orders.html', orders=user_orders)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES: Nạp tiền (Deposit)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/deposit')
@login_required
def deposit():
    """Trang nạp tiền: người dùng nhập số tiền và nhận mã QR."""
    return render_template('deposit.html')


# ─────────────────────────────────────────────────────────────────────────────
# API: Tạo giao dịch nạp tiền & sinh mã QR
# Thông tin tài khoản nhận tiền thật:
#   Ngân hàng : Techcombank
#   Số TK     : 88888808042007
#   Chủ TK    : LE CONG MINH
# ─────────────────────────────────────────────────────────────────────────────
BANK_ID      = 'Techcombank'
BANK_ACCOUNT = '88888808042007'
ACCOUNT_NAME = 'LE CONG MINH'

@app.route('/api/deposit/create', methods=['POST'])
@login_required
def api_deposit_create():
    """
    Tạo một bản ghi Transaction với trạng thái 'pending'.
    Trả về mã QR VietQR (Techcombank thật) và trans_code để frontend hiển thị.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Request body không hợp lệ (cần JSON)'}), 400

        amount = data.get('amount', 0)

        # Kiểm tra số tiền hợp lệ (tối thiểu 10,000đ)
        if not isinstance(amount, (int, float)) or amount < 10000:
            return jsonify({'success': False, 'message': 'So tien toi thieu la 10,000d'}), 400

        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Khong tim thay nguoi dung'}), 401

        # Sinh mã nội dung chuyển khoản duy nhất: NAP{user_id}_{4 chữ số ngẫu nhiên}
        rand_suffix = ''.join(random.choices(string.digits, k=4))
        trans_code  = f"NAP{user.id}_{rand_suffix}"

        # Tạo bản ghi giao dịch với trạng thái chờ
        txn = Transaction(
            user_id    = user.id,
            amount     = amount,
            trans_code = trans_code,
            status     = 'pending'
        )
        db.session.add(txn)
        db.session.commit()
        print(f"[DEPOSIT] Tao giao dich: {trans_code} | {int(amount)}d | user_id={user.id}")

        # ── Tạo URL QR VietQR với tài khoản Techcombank thật ───────────────
        # Cấu trúc: https://img.vietqr.io/image/<BANK>-<STK>-compact2.png?amount=...&addInfo=...&accountName=...
        # addInfo và accountName cần URL-encode để xử lý ký tự đặc biệt / khoảng trắng
        from urllib.parse import quote
        qr_url = (
            f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-compact2.png"
            f"?amount={int(amount)}"
            f"&addInfo={quote(trans_code)}"
            f"&accountName={quote(ACCOUNT_NAME)}"
        )

        return jsonify({
            'success'      : True,
            'trans_code'   : trans_code,
            'amount'       : amount,
            'qr_url'       : qr_url,
            'bank_id'      : BANK_ID,
            'bank_account' : BANK_ACCOUNT,
            'account_name' : ACCOUNT_NAME,
        })

    except Exception as e:
        # In chi tiết lỗi ra terminal để dễ debug
        import traceback
        print(f"[ERROR] /api/deposit/create: {e}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Loi server: {str(e)}'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# API: Kiểm tra trạng thái giao dịch (dùng cho polling tự động trên giao diện)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/deposit/check-status/<trans_code>')
def api_deposit_check_status(trans_code):
    """
    Kiểm tra trạng thái của một giao dịch nạp tiền (pending hoặc success).
    Giao diện gọi tự động mỗi 2 giây sau khi tạo mã QR.
    Không yêu cầu login_required để tránh lỗi hết hạn session cookie.
    """
    txn = Transaction.query.filter_by(trans_code=trans_code).first()

    if not txn:
        return jsonify({'success': False, 'message': 'Không tìm thấy giao dịch'}), 404

    user = User.query.get(txn.user_id)
    balance = user.balance if user else 0
    return jsonify({
        'success'        : True,
        'trans_code'     : txn.trans_code,
        'status'         : txn.status,          # 'pending' hoặc 'success'
        'amount'         : txn.amount,
        'amount_fmt'     : format_vnd(txn.amount),
        'new_balance'    : balance,
        'new_balance_fmt': format_vnd(balance),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API: Webhook nhận callback thanh toán từ ngân hàng (SePay, Casso, App SMS, hoặc Test)
# ─────────────────────────────────────────────────────────────────────────────

import re

def safe_log(msg):
    """In log ra terminal an toàn tuyệt đối trên Windows cp1252, không bao giờ bị lỗi charmap unicode."""
    try:
        clean = str(msg).encode('ascii', errors='replace').decode('ascii')
        print(clean, flush=True)
    except Exception:
        pass


@app.route('/api/webhook/payment', methods=['POST'])
@app.route('/api/webhook/payment ', methods=['POST'])
@app.route('/api/webhook/payr', methods=['POST'])
@app.route('/api/webhook/payr ', methods=['POST'])
@app.route('/api/webhook', methods=['POST'])
@app.route('/api/webhook ', methods=['POST'])
def api_webhook_payment():
    """
    Webhook xử lý khi ngân hàng hoặc MacroDroid báo chuyển khoản thành công.
    Tự động trích xuất mã NAP... từ mọi dữ liệu nhận được (JSON, form, raw text...).
    """
    try:
        raw_text = request.get_data(as_text=True) or ''
        data = request.get_json(force=True, silent=True) or {}
        if request.form:
            data.update(request.form.to_dict())

        # Gộp tất cả các chuỗi text có thể có vào một xâu tổng để tìm mã NAP
        search_corpus = f"{raw_text} {str(data)}"
        safe_log(f"[WEBHOOK IN] Nhan du lieu dai {len(search_corpus)} ky tu")

        # Ghi vao file debug de kiem tra chinh xac noi dung dien thoai gui ve
        try:
            with open(os.path.join(BASE_DIR, 'webhook_debug.log'), 'a', encoding='utf-8') as f:
                f.write(f"--- {datetime.now()} ---\n")
                f.write(f"CORPUS: {search_corpus}\n\n")
        except Exception:
            pass

        # 1. Tìm trực tiếp mã có dạng NAP<user_id>_<suffix> trong nội dung bằng Regex
        match = re.search(r'NAP\d+[\s_\-]?\d+', search_corpus, re.IGNORECASE)
        found_code = None
        if match:
            # Chuẩn hóa về dạng NAP{uid}_{rand}
            m_str = match.group(0).upper()
            m_parts = re.split(r'[\s_\-]+', m_str)
            if len(m_parts) == 2:
                found_code = f"{m_parts[0]}_{m_parts[1]}"
            else:
                found_code = m_str

        txn = None
        if found_code:
            safe_log(f"[WEBHOOK] Tim thay ma qua Regex: {found_code}")
            txn = Transaction.query.filter_by(trans_code=found_code, status='pending').first()

        # 2. Quét danh sách pending để so khớp mềm (bỏ qua dấu cách, gạch dưới, gạch ngang)
        if not txn:
            normalized_corpus = re.sub(r'[\s_\-]', '', search_corpus).upper()
            pending_txns = Transaction.query.filter_by(status='pending').order_by(Transaction.id.desc()).all()
            for p_txn in pending_txns:
                norm_code = re.sub(r'[\s_\-]', '', p_txn.trans_code).upper()
                if norm_code in normalized_corpus:
                    txn = p_txn
                    safe_log(f"[WEBHOOK] Tim thay ma qua so khop mem: {txn.trans_code}")
                    break

        # 3. DỰ PHÒNG: Nếu vẫn chưa thấy mã NAP (do Techcombank cắt ngắn nội dung),
        # trích xuất số tiền trong thông báo và tìm giao dịch pending gần nhất (trong vòng 15 phút)
        if not txn:
            # Tìm số tiền dạng: +20,000 hoặc +20.000 hoặc +20000 hoặc 20000
            money_matches = re.findall(r'[\+]?([0-9]{1,3}(?:[,\.][0-9]{3})+|[0-9]{4,9})', search_corpus)
            extracted_amounts = []
            for m in money_matches:
                clean_num = re.sub(r'[,.]', '', m)
                try:
                    val = float(clean_num)
                    if val >= 10000:
                        extracted_amounts.append(val)
                except ValueError:
                    pass

            safe_log(f"[WEBHOOK] Cac so tien trich xuat duoc: {extracted_amounts}")
            # Tìm giao dịch pending gần nhất khớp số tiền
            if extracted_amounts:
                for amt in extracted_amounts:
                    candidate = Transaction.query.filter_by(amount=amt, status='pending').order_by(Transaction.id.desc()).first()
                    if candidate:
                        txn = candidate
                        safe_log(f"[WEBHOOK] Khop du phong theo so tien {amt}d -> Giao dich: {txn.trans_code}")
                        break

        if not txn:
            safe_log("[WEBHOOK] Khong tim thay giao dich pending phu hop trong database")
            return jsonify({'success': False, 'message': 'Khong tim thay giao dich pending'}), 400

        # ── CỘNG TIỀN VÀO TÀI KHOẢN NGƯỜI DÙNG ──────────────────────────
        user = User.query.get(txn.user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Khong tim thay user'}), 404

        txn.status = 'success'
        user.balance += txn.amount
        db.session.commit()

        safe_log(f"[WEBHOOK SUCCESS] Da cong {int(txn.amount)}d vao tai khoan '{user.username}'. So du moi: {int(user.balance)}d")

        return jsonify({
            'success'        : True,
            'message'        : f'Nạp tiền thành công! +{format_vnd(txn.amount)}',
            'new_balance'    : user.balance,
            'new_balance_fmt': format_vnd(user.balance),
        })

    except Exception as e:
        db.session.rollback()
        safe_log(f"[WEBHOOK ERROR] Exception: {str(e)}")
        return jsonify({'success': False, 'message': f'Loi webhook: {str(e)}'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# API: Lấy số dư hiện tại (dùng cho AJAX cập nhật Navbar)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/user/balance')
@login_required
def api_user_balance():
    """Trả về số dư hiện tại của người dùng đã đăng nhập."""
    user = get_current_user()
    return jsonify({
        'balance'    : user.balance,
        'balance_fmt': format_vnd(user.balance),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API: Thanh toán giỏ hàng bằng số dư tài khoản
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def api_cart_checkout():
    """
    Xử lý thanh toán giỏ hàng bằng số dư tài khoản.
    Nhận JSON: { "items": [{"product_id": 1, "quantity": 2}, ...] }

    Luồng xử lý:
      1. Tính tổng tiền dựa trên giá từ DB (không tin giá từ client).
      2. Kiểm tra stock còn đủ không.
      3. Kiểm tra balance >= total_amount.
         - Đủ tiền  → Trừ balance, trừ stock, tạo Order + OrderItems → 200.
         - Thiếu tiền → 402 kèm thông báo chuyển sang trang nạp tiền.
    """
    data  = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'message': 'Giỏ hàng trống'}), 400

    user = get_current_user()

    # ── Bước 1: Validate sản phẩm và tính tổng tiền từ DB ──────────────────
    order_items_data = []
    total_amount     = 0.0

    for item in items:
        product_id = item.get('product_id')
        quantity   = item.get('quantity', 1)

        if not product_id or quantity < 1:
            return jsonify({'success': False, 'message': 'Dữ liệu giỏ hàng không hợp lệ'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': f'Sản phẩm #{product_id} không tồn tại'}), 404

        # Kiểm tra tồn kho
        if product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Sản phẩm "{product.name}" chỉ còn {product.stock} trong kho'
            }), 400

        subtotal      = product.price * quantity
        total_amount += subtotal
        order_items_data.append({
            'product'   : product,
            'quantity'  : quantity,
            'unit_price': product.price,
        })

    # ── Bước 2: Kiểm tra số dư tài khoản ────────────────────────────────────
    if user.balance < total_amount:
        deficit = total_amount - user.balance
        return jsonify({
            'success'     : False,
            'need_deposit': True,
            'message'     : f'Số dư không đủ! Bạn cần nạp thêm {format_vnd(deficit)} để thanh toán.',
            'deposit_url' : url_for('deposit'),
        }), 402

    # ── Bước 3: Trừ tiền & trừ stock, tạo đơn hàng ─────────────────────────
    user.balance -= total_amount   # Trừ tiền từ số dư tài khoản

    new_order = Order(
        user_id      = user.id,
        total_amount = total_amount,
        status       = 'success'
    )
    db.session.add(new_order)
    db.session.flush()  # Lấy new_order.id trước khi commit

    for item_data in order_items_data:
        product  = item_data['product']
        quantity = item_data['quantity']

        # Bốc đúng số lượng tài khoản game còn trong kho gán vào đơn hàng
        available_accs = GameAccount.query.filter_by(product_id=product.id, status='available').limit(quantity).all()
        for acc in available_accs:
            acc.status = 'sold'
            acc.order_id = new_order.id
            acc.sold_at = datetime.utcnow()

        # Đồng bộ tồn kho: nếu sản phẩm có acc trong kho thì cập nhật theo số lượng available thực tế
        has_accs = GameAccount.query.filter_by(product_id=product.id).count() > 0
        if has_accs:
            product.stock = GameAccount.query.filter_by(product_id=product.id, status='available').count()
        else:
            product.stock = max(0, product.stock - quantity)

        order_item = OrderItem(
            order_id   = new_order.id,
            product_id = product.id,
            quantity   = quantity,
            unit_price = item_data['unit_price'],
        )
        db.session.add(order_item)

    db.session.commit()
    # ────────────────────────────────────────────────────────────────────────

    return jsonify({
        'success'        : True,
        'message'        : f'🎉 Đặt hàng thành công! Tổng: {format_vnd(total_amount)}',
        'order_id'       : new_order.id,
        'new_balance'    : user.balance,
        'new_balance_fmt': format_vnd(user.balance),
    })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES: Quản trị viên (Admin Control Panel)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Trang chủ quản trị: thống kê doanh thu, đơn hàng, kho acc game, thành viên."""
    products = Product.query.order_by(Product.id.asc()).all()
    users = User.query.order_by(User.id.desc()).all()
    recent_orders = Order.query.order_by(Order.id.desc()).limit(15).all()
    recent_transactions = Transaction.query.order_by(Transaction.id.desc()).limit(15).all()
    all_accounts = GameAccount.query.order_by(GameAccount.id.desc()).all()

    # Thống kê tổng quan
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(status='success').scalar() or 0.0
    total_orders = Order.query.count()
    total_users = User.query.count()
    total_acc_available = GameAccount.query.filter_by(status='available').count()
    total_acc_sold = GameAccount.query.filter_by(status='sold').count()

    return render_template('admin.html',
                           products=products,
                           users=users,
                           recent_orders=recent_orders,
                           recent_transactions=recent_transactions,
                           all_accounts=all_accounts,
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_acc_available=total_acc_available,
                           total_acc_sold=total_acc_sold)


@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_product_add():
    """Thêm sản phẩm danh mục mới."""
    name = request.form.get('name', '').strip()
    price = request.form.get('price', type=float)
    image_url = request.form.get('image_url', '').strip()
    description = request.form.get('description', '').strip()

    if not name or price is None or price < 0:
        flash('Vui lòng nhập tên và giá sản phẩm hợp lệ.', 'error')
        return redirect(url_for('admin_dashboard'))

    if not image_url:
        image_url = 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&h=400&fit=crop'

    product = Product(name=name, price=price, image_url=image_url, description=description, stock=0)
    db.session.add(product)
    db.session.commit()
    flash(f'Đã thêm sản phẩm "{name}" thành công!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/products/edit/<int:product_id>', methods=['POST'])
@admin_required
def admin_product_edit(product_id):
    """Sửa thông tin sản phẩm (tên, giá, mô tả, ảnh)."""
    product = Product.query.get_or_404(product_id)
    product.name = request.form.get('name', product.name).strip()
    product.price = request.form.get('price', type=float) or product.price
    product.image_url = request.form.get('image_url', product.image_url).strip()
    product.description = request.form.get('description', product.description).strip()
    db.session.commit()
    flash(f'Đã cập nhật sản phẩm "{product.name}"!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_product_delete(product_id):
    """Xóa sản phẩm."""
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Đã xóa sản phẩm "{name}"!', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/accounts/add', methods=['POST'])
@admin_required
def admin_account_add():
    """
    Thêm tài khoản acc game vào kho của sản phẩm.
    Hỗ trợ nhập hàng loạt: mỗi dòng là 1 tài khoản (ví dụ: tk|mk hoặc tài khoản chi tiết).
    Tự động cập nhật số lượng tồn kho (stock) của sản phẩm.
    """
    product_id = request.form.get('product_id', type=int)
    accounts_text = request.form.get('accounts_text', '').strip()

    product = Product.query.get(product_id)
    if not product:
        flash('Sản phẩm không tồn tại.', 'error')
        return redirect(url_for('admin_dashboard'))

    if not accounts_text:
        flash('Vui lòng nhập ít nhất một tài khoản.', 'error')
        return redirect(url_for('admin_dashboard'))

    lines = [line.strip() for line in accounts_text.splitlines() if line.strip()]
    added_count = 0
    for line in lines:
        acc = GameAccount(
            product_id=product.id,
            account_info=line,
            status='available'
        )
        db.session.add(acc)
        added_count += 1

    db.session.flush()
    # Tự động cập nhật tồn kho theo số lượng acc available thực tế
    product.stock = GameAccount.query.filter_by(product_id=product.id, status='available').count()
    db.session.commit()

    flash(f'Đã nạp thành công {added_count} tài khoản vào "{product.name}". Tồn kho hiện tại: {product.stock}', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/accounts/delete/<int:account_id>', methods=['POST'])
@admin_required
def admin_account_delete(account_id):
    """Xóa một tài khoản chưa bán khỏi kho."""
    acc = GameAccount.query.get_or_404(account_id)
    if acc.status == 'sold':
        flash('Không thể xóa tài khoản đã được bán cho khách hàng!', 'error')
        return redirect(url_for('admin_dashboard'))

    product = Product.query.get(acc.product_id)
    db.session.delete(acc)
    db.session.flush()
    if product:
        product.stock = GameAccount.query.filter_by(product_id=product.id, status='available').count()
    db.session.commit()
    flash('Đã xóa tài khoản khỏi kho.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/adjust-balance', methods=['POST'])
@admin_required
def admin_user_adjust_balance():
    """Admin cộng hoặc trừ số dư trực tiếp cho thành viên."""
    user_id = request.form.get('user_id', type=int)
    amount = request.form.get('amount', type=float)
    action = request.form.get('action', 'add')

    user = User.query.get(user_id)
    if not user:
        flash('Không tìm thấy người dùng.', 'error')
        return redirect(url_for('admin_dashboard'))

    if not amount or amount <= 0:
        flash('Vui lòng nhập số tiền hợp lệ (> 0).', 'error')
        return redirect(url_for('admin_dashboard'))

    if action == 'sub':
        user.balance = max(0.0, user.balance - amount)
        flash(f'Đã trừ {format_vnd(amount)} của thành viên {user.username}. Số dư mới: {format_vnd(user.balance)}', 'info')
    else:
        user.balance += amount
        flash(f'Đã cộng {format_vnd(amount)} cho thành viên {user.username}. Số dư mới: {format_vnd(user.balance)}', 'success')

    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("[OK] Shop Ban Hang dang chay tai http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
