from flask import Flask, render_template, request, redirect, url_for,Response, jsonify, session
import pytz
from flask import flash
from flask_migrate import Migrate

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jsodnc-28u3nJ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sas.db'
db = SQLAlchemy(app)
migrate = Migrate(app,db)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.String(20), nullable=False) 
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Kolkata'))) 
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Kolkata')), onupdate=datetime.now(pytz.timezone('Asia/Kolkata')))
    purchase_price = db.Column(db.Float, nullable=False) 
    
class ItemTransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item', backref=db.backref('transactions', lazy=True))
    transaction_type = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Kolkata')))
    transaction_quantity = db.Column(db.Integer, nullable=False)
    transaction_price = db.Column(db.Float, nullable=False)
    
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User username={self.username} email={self.email} role={self.role}>'



     #db.create_all()
     




@app.route('/')
def home():
    return render_template('home.html')
    
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            if user.role == 'manager':
                return redirect(url_for('manager'))
            elif user.role == 'inventory-management-staff':
                return redirect(url_for('inventory_management_staff'))
            elif user.role == 'salesclerk':
                return redirect(url_for('sales_clerk'))
        else:
            flash('Invalid login credentials.')

    return render_template('login.html')
    

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']

        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('A user with that username already exists.')
            return redirect(url_for('signup'))

        
        new_user = User(username=username, password=password, email=email ,role=role)
        db.session.add(new_user) 
        db.session.commit()

        flash('Sign up successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')
    
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))



@app.route('/manager')
def manager():
    return render_template('manager.html')
    
@app.route('/manager/change_price', methods=['GET', 'POST'])
def change_price():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_id = request.form['item_id']
        new_price = request.form['new_price']
        
        
        item = Item.query.filter_by(name=item_name, id=item_id).first()
        
        if item:
            # Update the item's price in the database
            item.price = new_price
            db.session.commit()
            
            flash('Price updated successfully!')
            return redirect(url_for('manager'))
        else:
            flash('Item not found!')
    
    return render_template('change_price.html')
    
    

@app.route('/inventory-management-staff')
def inventory_management_staff():
    items = Item.query.all()
    return render_template('add_product.html', items=items)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        item_name = request.form['name']
        item_id = request.form['id']
        item_quantity = int(request.form['quantity'])
        item_price = float(request.form['price'])
        item_purchaseprice = float(request.form['purchaseprice'])
        item_type = request.form['type']

        
        if item_type == 'Packaged':
            item_quantity = item_quantity  
        elif item_type == 'Loose':
            item_quantity = item_quantity * 1000  

        item = Item.query.filter_by(id=item_id).first()
        if item is None:
            item = Item(id=item_id, name=item_name, price=item_price, quantity=item_quantity, type=item_type, created_at=datetime.now(pytz.timezone('Asia/Kolkata')), updated_at=datetime.now(pytz.timezone('Asia/Kolkata')),purchase_price=item_purchaseprice)
            db.session.add(item)
        else:
            item.quantity += item_quantity
            item.last_updated = datetime.now(pytz.timezone('Asia/Kolkata'))

        db.session.commit()

        items = Item.query.all()
        return render_template('add_product.html', items=items)

    return render_template('add_product.html')
    
@app.route('/view_sales_statistics', methods=['GET', 'POST'])
def view_sales_statistics():
  if request.method == 'POST':
    item_name = request.form['item_name']
    start_date = request.form['start_date']
    start_time = request.form['start_time']
    end_date = request.form['end_date']
    end_time = request.form['end_time']

    start_datetime = datetime.strptime(start_date + ' ' + start_time, '%Y-%m-%d %I:%M %p')
    end_datetime = datetime.strptime(end_date + ' ' + end_time, '%Y-%m-%d %I:%M %p')

    item = Item.query.filter_by(name=item_name).first()
    if not item:
       flash(f'Item "{item_name}" not found!', 'error')
       return redirect(url_for('view_sales_statistics'))

    item_transactions = db.session.query(ItemTransactionHistory).filter(
       ItemTransactionHistory.item_id == item.id,
       ItemTransactionHistory.transaction_date >= start_datetime,
       ItemTransactionHistory.transaction_date <= end_datetime
    ).all()
    total_sales = sum(transaction.transaction_price for transaction in item_transactions)
    quantity_sold = sum(transaction.transaction_quantity for transaction in item_transactions)
    total_profit = total_sales - (quantity_sold * item.purchase_price)

    sales_stats = {
        'quantity': quantity_sold,
        'total_sales': total_sales,
        'total_profit': total_profit
    }

    return render_template('sales_statistics.html', item_name=item_name, start_date=start_date, start_time=start_time, end_date=end_date, end_time=end_time, sales_stats=sales_stats)

  return render_template('sales_statistics.html')

@app.route('/sales_clerk', methods=['GET', 'POST'])
def sales_clerk():
    items = Item.query.all()
    if request.method == 'POST':
        item_ids = request.form.getlist('item_id')
        item_quantities = request.form.getlist('item_quantity')
        total_cost = 0
        transactions = []
        for i in range(len(item_ids)):
            item_id = int(item_ids[i])
            item_quantity = int(item_quantities[i])
            item = Item.query.get(item_id)
            if item and item.quantity >= item_quantity:
                
                transaction = ItemTransactionHistory(
                    item_id=item_id,
                    item=item,
                    transaction_type='Sale',
                    transaction_quantity=item_quantity,
                    transaction_price=item.price * item_quantity
                )
                db.session.add(transaction)
                transactions.append(transaction)
                
                item.quantity -= item_quantity
                total_cost += transaction.transaction_price
        if total_cost > 0:
            db.session.commit()
            return render_template('sales_clerk_receipt.html', transactions=transactions, total_cost=total_cost)
        else:
            flash('One or more items are out of stock!')
    return render_template('salesclerk.html', items=items)





@app.route('/view_inventory')
def view_inventory():
    
    items = Item.query.all()
    return render_template('view_inventory.html', items=items)
    
   

@app.route('/new transaction')    
def new_transaction():
    return 'This is new transaction page'   

if __name__ == '__main__':
    with app.app_context():
       db.create_all()
    app.run(debug=True)

