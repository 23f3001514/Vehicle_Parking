from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__) 

app.secret_key = 'secret_key_for_session' #use to store data in session without this flask can't store details in session , keeps track to logged in-users
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///Parking.db'

db = SQLAlchemy(app) # it is used to connect flask app to database using sqlalchemy

#Admin Model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable = False)
    password = db.Column(db.Integer, nullable = False, unique = True)


#USER MODEL
class User(db.Model):
    id = db.Column(db.Integer() , primary_key=True)
    username = db.Column(db.String(50) , nullable = False ,unique = True)
    full_name = db.Column(db.String(100) , nullable = False)
    password = db.Column(db.String(100) , nullable = False)
    address = db.Column(db.String(100) , nullable = True)
    pin_code = db.Column(db.String(100) , nullable = False)



#Parking Lot Model
class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False , unique = True)
    address = db.Column(db.String(100), nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete-orphan", lazy=True)


#Parking Spot Model
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False) # each parking spot is linked to Parking lot using lot_id
    spot_number = db.Column(db.String(50), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    booked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)







#Home Page
@app.route('/')
def home():
    return render_template('index.html')



#USER REGISTER
@app.route('/user/register', methods=['GET' , 'POST'])
def user_register():
    if request.method == "POST":
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        address = request.form['address']
        pin_code = request.form['pin_code']

        if User.query.filter_by(username=username).first():
            return render_template('user_register.html', error = "Username Already Exists!")
        
        user = User(username = username, full_name = full_name, password = password, address = address, pin_code = pin_code)
        db.session.add(user)
        db.session.commit()
        return redirect('/user/login')
    return render_template('user_register.html')


@app.route('/user/login' , methods = ['GET' , 'POST'])
def user_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username , password=password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username

            return redirect('/user/dashboard')
        
        return render_template('user_login.html' , error = "Entered Details are Invalid!")
    
    return render_template('user_login.html')



#BOOK SPOT
@app.route('/user/book_spot/<int:spot_id>')
def book_spot(spot_id):
    if "user_id" not in session:
        return redirect('/user/login')
    
    spot = ParkingSpot.query.get_or_404(spot_id)

    if spot.is_occupied:
        return "Spot Already Booked!", 400
    
    spot.is_occupied = True
    spot.booked_by = session['user_id']
    db.session.commit()

    return redirect('/user/dashboard')



#CANCEL BOOKING
@app.route('/user/cancel_booking/<int:spot_id>')
def cancel_spot(spot_id):
    if "user_id" not in session:
        return redirect('/user/login')
    
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if spot.booked_by != session['user_id']:
        return "You can Cancel your own Bookings!", 403
    
    spot.is_occupied = False
    spot.booked_by = None
    db.session.commit()

    return redirect('/user/dashboard')



#EDIT LOT
@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        lot.location_name = request.form['location_name']
        lot.address = request.form['address']
        new_total = int(request.form['total_spots'])

        # Delete all old spots for this lot
        ParkingSpot.query.filter_by(lot_id=lot.id).delete()

        # Add new spots as per updated total
        for i in range(1, new_total + 1):
            new_spot = ParkingSpot(lot_id=lot.id, spot_number=str(i), is_occupied=False)
            db.session.add(new_spot)

        lot.total_spots = new_total
        db.session.commit()
        return redirect('/admin/dashboard')

    return render_template('edit_lot.html', lot=lot)



#ADMIN LOGIN
@app.route('/admin/login' , methods=['GET' , 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username = username, password = password).first()

        if admin:
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect('/admin/dashboard')
        else:
            return render_template('admin_login.html', error = "Entered Deatils Are Invalid!")
    return render_template('admin_login.html')




#USER DASHBOARD
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/user/login')
    
    search_query = request.args.get('search' ,'').strip().lower()

    if search_query:
        lots = ParkingLot.query.filter(
            ParkingLot.location_name.ilike(f'%{ search_query }%') | 
            ParkingLot.address.ilike(f'%{ search_query }%')
        ).all()
    else:
        lots = ParkingLot.query.all()

    return render_template('user_dashboard.html', username=session.get('user_username'), lots=lots, search_query=search_query)
    
    


#ADMIN DASHBOARD
@app.route('/admin/dashboard' , methods = ['GET' , 'POST'])
def admin_dashboard():
    if "admin_id" not in session:
        return redirect('/admin/login')
    
    search_query = request.args.get('search' ,'').strip().lower()

    if search_query:
        lots = ParkingLot.query.filter(
            ParkingLot.location_name.ilike(f'%{ search_query }%') |
            ParkingLot.address.ilike(f'%{ search_query }%')
        ).all()
    else:
        lots = ParkingLot.query.all()

    for lot in lots:
        for spot in lot.spots:
            spot.booked_user = User.query.get(spot.booked_by) if spot.is_occupied else None

    return render_template('admin_dashboard.html' , lots=lots, search_query=search_query,username=session.get("admin_username"))





#CREATE LOT
@app.route('/admin/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    if request.method == 'POST':
        location_name = request.form['location_name']
        address = request.form['address']
        total_spots = int(request.form['total_spots'])

        if ParkingLot.query.filter_by(location_name=location_name , address=address).first():
            return render_template('create_lot.html' , error = "Lot with this name already exists!")
        
        lot = ParkingLot(location_name=location_name, address=address, total_spots=total_spots)
        db.session.add(lot)
        db.session.commit()

        for i in range(1, total_spots + 1):
            spot = ParkingSpot(lot_id=lot.id, spot_number=str(i))
            db.session.add(spot)
        db.session.commit()

        return redirect('/admin/dashboard')

    return render_template('create_lot.html')


#DELETE LOT
@app.route('/admin/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()

    return redirect('/admin/dashboard')


#USER DETAILS
@app.route('/admin/user_detail/<int:user_id>')
def user_detail(user_id):
    if "admin_id" not in session:
        return redirect('/admin/login')
    
    user = User.query.get_or_404(user_id)
    
    return render_template('user_detail.html' , user=user)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            default_admin = Admin(username='admin', password='admin123')
            db.session.add(default_admin)
            db.session.commit()
    app.run(debug=True)





