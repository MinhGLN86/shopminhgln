# database.py — Khởi tạo DB và seed 8 sản phẩm mẫu lần đầu chạy

from models import db, Product

# Danh sách 8 sản phẩm mẫu với hình từ Unsplash (kích thước 600x400)
SAMPLE_PRODUCTS = [
    {
        "name": "Tai nghe Sony WH-1000XM5",
        "price": 8990000,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=400&fit=crop",
        "description": "Tai nghe chống ồn hàng đầu với chất lượng âm thanh vượt trội, thời lượng pin 30h và kết nối Bluetooth 5.2.",
        "stock": 15
    },
    {
        "name": "Apple Watch Series 9",
        "price": 12500000,
        "image_url": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=600&h=400&fit=crop",
        "description": "Đồng hồ thông minh Apple Watch Series 9 với chip S9, màn hình Always-On Retina, theo dõi sức khỏe toàn diện.",
        "stock": 10
    },
    {
        "name": "Bàn phím cơ Keychron K2",
        "price": 2200000,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&h=400&fit=crop",
        "description": "Bàn phím cơ compact 75%, switch Gateron, kết nối đa thiết bị Bluetooth + USB-C, tương thích Mac/Windows.",
        "stock": 25
    },
    {
        "name": "Chuột Logitech MX Master 3S",
        "price": 1850000,
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&h=400&fit=crop",
        "description": "Chuột không dây cao cấp, cuộn MagSpeed siêu mượt, cảm biến 8000 DPI, hoạt động trên mọi bề mặt.",
        "stock": 30
    },
    {
        "name": "Loa Bluetooth JBL Charge 5",
        "price": 3400000,
        "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&h=400&fit=crop",
        "description": "Loa di động chống nước IP67, âm thanh mạnh mẽ 40W, pin 20h, kiêm sạc dự phòng cho điện thoại.",
        "stock": 20
    },
    {
        "name": "Đèn bàn LED Thông minh",
        "price": 450000,
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=400&fit=crop",
        "description": "Đèn bàn LED điều chỉnh độ sáng và màu sắc, chế độ đọc sách bảo vệ mắt, cổng sạc USB tích hợp.",
        "stock": 50
    },
    {
        "name": "Túi đựng Laptop 15.6\"",
        "price": 320000,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=400&fit=crop",
        "description": "Túi chống sốc cao cấp cho laptop đến 15.6 inch, chất liệu Oxford bền, nhiều ngăn tiện lợi.",
        "stock": 40
    },
    {
        "name": "Hub USB-C 7-in-1",
        "price": 680000,
        "image_url": "https://images.unsplash.com/photo-1625842268584-8f3296236761?w=600&h=400&fit=crop",
        "description": "Hub USB-C mở rộng cổng: HDMI 4K, USB-A x3, SD/TF Card, sạc PD 100W, hỗ trợ MacBook và laptop mỏng.",
        "stock": 35
    },
]


def seed_products():
    """Thêm sản phẩm mẫu vào DB nếu bảng products còn trống.
    !! Đã tắt auto-seed — bỏ comment khối bên dưới nếu muốn seed lại !!
    """
    # if Product.query.count() == 0:
    #     for p in SAMPLE_PRODUCTS:
    #         product = Product(**p)
    #         db.session.add(product)
    #     db.session.commit()
    #     print(f"[DB] Da seed {len(SAMPLE_PRODUCTS)} san pham mau.")
    # else:
    #     print("[DB] Bang products da co du lieu, bo qua buoc seed.")
    pass  # Auto-seed da duoc tat
