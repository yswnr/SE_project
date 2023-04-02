from flask import Flask, render_template, request, redirect, url_for,Response, jsonify
#from decimal import Decimal
from flask import flash
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jsodnc-28u3nJ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sas.db'
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.String(20), nullable=False) # Added type column
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Added created_at column
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) # Added updated_at column with onupdate=datetime.utcnow to update automatically
    
    

class ItemTransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item', backref=db.backref('transaction_history', lazy=True))
    transaction_type = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transaction_quantity = db.Column(db.Integer, nullable=False)
    transaction_price = db.Column(db.Float, nullable=False)

#class In    
    
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User username={self.username} role={self.role}>'


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




@app.route('/manager')
def manager():
    return render_template('manager.html')
    
@app.route('/manager/change_price', methods=['GET', 'POST'])
def change_price():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_id = request.form['item_id']
        new_price = request.form['new_price']
        
        # Query the Item table for the item with the given name and id
        item = Item.query.filter_by(name=item_name, id=item_id).first()
        
        if item:
            # Update the item's price in the database
            item.price = new_price
            db.session.commit()
            
            flash('Price updated successfully!')
            return redirect(url_for('home'))
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
        item_type = request.form['type']

        # Convert quantity to appropriate units
        if item_type == 'Packaged':
            item_quantity = item_quantity  # Keep in units
        elif item_type == 'Loose':
            item_quantity = item_quantity * 1000  # Convert to grams

        item = Item.query.filter_by(id=item_id).first()
        if item is None:
            item = Item(id=item_id, name=item_name, price=item_price, quantity=item_quantity, type=item_type, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            db.session.add(item)
        else:
            item.quantity += item_quantity
            item.last_updated = datetime.utcnow()

        db.session.commit()

        items = Item.query.all()
        return render_template('add_product.html', items=items)

    return render_template('add_product.html')

@app.route('/sales-clerk')
def sales_clerk():
    return render_template('salesclerk.html')


@app.route('/view-sales-statistics')
def view_sales_statistics():
    return 'This is the view sales statistics page.'

@app.route('/view_inventory')
def view_inventory():
    items = Item.query.all()
    return render_template('view_inventory.html', items=items)
    
   

@app.route('/new_transaction', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        item_id = request.form['id']
        quantity = int(request.form['quantity'])

        # Retrieve item from database
        item = Item.query.filter_by(id=item_id).first()

        # Calculate transaction price
        transaction_price = item.price * quantity

        # Update inventory quantity
        item.quantity -= quantity
        db.session.commit()

        # Record transaction history
        transaction = ItemTransactionHistory(item=item, transaction_type='sale', transaction_quantity=quantity, transaction_price=transaction_price)
        db.session.add(transaction)
        db.session.commit()

        return render_template('transaction_complete.html', item=item, quantity=quantity, transaction_price=transaction_price)

    return render_template('new_transaction.html')


 

if __name__ == '__main__':
    with app.app_context():
       db.create_all()
    app.run(debug=True)

