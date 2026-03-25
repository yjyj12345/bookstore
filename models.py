from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 图书模型
class Book(db.Model):
    __tablename__ = 'book'
    BookID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookname = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255))
    Introduction = db.Column(db.Text)
    Inventory = db.Column(db.Integer, default=0)
    NewPurchase = db.Column(db.Integer, default=0)
    PurchasePrice = db.Column(db.Float)
    SellingPrice = db.Column(db.Float)
    sales = db.relationship('SalesRecord', backref='book', lazy=True)

# 销售记录模型
class SalesRecord(db.Model):
    __tablename__ = 'sales_record'
    SaleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)
    sell_date = db.Column(db.DateTime, default=datetime.utcnow)
    sell_number = db.Column(db.Integer, nullable=False)