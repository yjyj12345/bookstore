from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from models import db, Book, SalesRecord

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:YJyyds%40050611@localhost:3306/bookstore'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'

db.init_app(app)


# 首页
@app.route('/')
def index():
    # 计算关键指标
    total_books = Book.query.count()

    # 今日销售额
    today = date.today()
    today_sales = db.session.query(
        db.func.sum(SalesRecord.sell_number * Book.SellingPrice)
    ).join(Book).filter(
        db.func.date(SalesRecord.sell_date) == today
    ).scalar() or 0.0

    # 低库存图书数量
    low_stock_count = Book.query.filter(Book.Inventory < 10).count()

    # 最近销售记录
    recent_sales = SalesRecord.query.join(Book).order_by(
        SalesRecord.sell_date.desc()
    ).limit(5).all()

    # 获取低库存图书列表（用于首页展示）
    low_stock_books = Book.query.filter(Book.Inventory < 10).limit(3).all()

    return render_template('index.html',
                           total_books=total_books,
                           today_sales=today_sales,
                           low_stock_count=low_stock_count,
                           low_stock_books=low_stock_books,
                           recent_sales=recent_sales)


# 图书管理
@app.route('/books')
def books_list():
    # 支持搜索功能
    search_query = request.args.get('q')
    if search_query:
        books = Book.query.filter(
            Book.bookname.ilike(f'%{search_query}%')
        ).all()
    else:
        books = Book.query.all()

    return render_template('books/list.html', books=books)


@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # 创建新书对象
        book = Book(
            bookname=request.form['bookname'],
            type=request.form['type'],
            Introduction=request.form['introduction'],
            Inventory=int(request.form['inventory']),
            NewPurchase=int(request.form['new_purchase']),
            PurchasePrice=float(request.form['purchase_price']),
            SellingPrice=float(request.form['selling_price'])
        )

        db.session.add(book)
        db.session.commit()
        flash('图书添加成功!', 'success')
        return redirect(url_for('books_list'))

    return render_template('books/add.html')


@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    book = Book.query.get_or_404(id)

    if request.method == 'POST':
        # 更新图书信息
        book.bookname = request.form['bookname']
        book.type = request.form['type']
        book.Introduction = request.form['introduction']
        book.Inventory = int(request.form['inventory'])
        book.NewPurchase = int(request.form['new_purchase'])
        book.PurchasePrice = float(request.form['purchase_price'])
        book.SellingPrice = float(request.form['selling_price'])

        db.session.commit()
        flash('图书更新成功!', 'success')
        return redirect(url_for('books_list'))

    return render_template('books/edit.html', book=book)


@app.route('/books/delete/<int:id>', methods=['POST'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('图书已删除!', 'success')
    return redirect(url_for('books_list'))


# 销售记录
@app.route('/sales')
def sales_list():
    sales = SalesRecord.query.join(Book).all()
    return render_template('sales/list.html', sales=sales)


@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        book_id = request.form['book_id']
        sell_number = int(request.form['sell_number'])

        # 检查库存
        book = Book.query.get_or_404(book_id)
        if book.Inventory < sell_number:
            flash('库存不足，无法完成销售!', 'error')
            return redirect(url_for('add_sale'))

        # 创建销售记录
        sale = SalesRecord(
            BookID=book_id,
            sell_number=sell_number,
            sell_date=datetime.strptime(request.form['sell_date'], '%Y-%m-%d')
        )

        # 更新库存
        book.Inventory -= sell_number

        db.session.add(sale)
        db.session.commit()
        flash('销售记录添加成功!', 'success')
        return redirect(url_for('sales_list'))

    # 获取所有可销售的图书
    books = Book.query.filter(Book.Inventory > 0).all()
    today = date.today().strftime('%Y-%m-%d')

    return render_template('sales/add.html', books=books, today=today)


# 统计分析
# 统计分析
@app.route('/stats')
def stats():
    # 计算总销售额
    total_sales = db.session.query(
        db.func.sum(SalesRecord.sell_number * Book.SellingPrice)
    ).join(Book).scalar() or 0

    # 畅销图书排行
    top_books = db.session.query(
        Book.bookname,
        db.func.sum(SalesRecord.sell_number).label('total_sold')
    ).join(SalesRecord).group_by(Book.BookID).order_by(
        db.desc('total_sold')
    ).limit(5).all()

    # 月度销售趋势 - 使用 MySQL 的 DATE_FORMAT 函数
    monthly_sales = db.session.query(
        db.func.date_format(SalesRecord.sell_date, '%Y-%m').label('month'),
        db.func.sum(SalesRecord.sell_number * Book.SellingPrice).label('total')
    ).join(Book).group_by('month').order_by('month').all()

    return render_template('stats/index.html',
                           total_sales=total_sales,
                           top_books=top_books,
                           monthly_sales=monthly_sales)

@app.route('/sales/delete/<int:id>', methods=['POST'])
def delete_sale(id):
    sale = SalesRecord.query.get_or_404(id)
    db.session.delete(sale)
    db.session.commit()
    return jsonify({'success': True, 'message': '销售记录已删除'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 创建所有表
    app.run(debug=True)