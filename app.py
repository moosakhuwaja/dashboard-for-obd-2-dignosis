from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import csv
import os
import pandas as pd
from forms import UploadForm
import plots
import glob
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class UserFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bulk_id = db.Column(db.String(50), nullable=False)
    car_reg_no = db.Column(db.String(20), nullable=False)
    vehicle_speed = db.Column(db.String, nullable=False)
    heading = db.Column(db.String, nullable=False)
    distance = db.Column(db.String, nullable=False)
    altitude = db.Column(db.String, nullable=False)
    o_s1_b1_voltage = db.Column(db.String, nullable=False)
    o_s2_b2_voltage = db.Column(db.String, nullable=False)
    o_s1_current = db.Column(db.String, nullable=False)
    calculated_engine_load = db.Column(db.String, nullable=False)
    engine_rpm = db.Column(db.String, nullable=False)
    spark_advance = db.Column(db.String, nullable=False)
    absolute_load_value = db.Column(db.String, nullable=False)
    throttle_position = db.Column(db.String, nullable=False)
    relative_throttle_position = db.Column(db.String, nullable=False)
    absolute_throttle_position = db.Column(db.String, nullable=False)
    ap_pos_d = db.Column(db.String, nullable=False)
    ap_pos_e = db.Column(db.String, nullable=False)
    commanded_exhaust_gas_recirculation = db.Column(db.String, nullable=False)
    commanded_evaporative_purge = db.Column(db.String, nullable=False)
    commanded_throttle_actuator = db.Column(db.String, nullable=False)
    fuel_rail_pressure = db.Column(db.String, nullable=False)
    o_s1_b1_fuel_air_equivalence_ratio = db.Column(db.String, nullable=False)
    fuel_tank_level_input = db.Column(db.String, nullable=False)
    o_s1_b1_fuelair_equivalence_ratio = db.Column(db.String, nullable=False)
    short_term_fuel_trim_b1 = db.Column(db.String, nullable=False)
    long_term_fuel_trim_b1 = db.Column(db.String, nullable=False)
    fuel_air_commanded_equivalence_ratio = db.Column(db.String, nullable=False)
    hybrid_battery_pack_remaining = db.Column(db.String, nullable=False)
    intake_manifold_absolute_pressure = db.Column(db.String, nullable=False)
    mass_air_flow_rate = db.Column(db.String, nullable=False)
    egr_error = db.Column(db.String, nullable=False)
    absolute_barometric_pressure = db.Column(db.String, nullable=False)
    engine_coolant_temperature = db.Column(db.String, nullable=False)
    intake_air_temperature = db.Column(db.String, nullable=False)
    catalyst_temperature_b1_s1 = db.Column(db.String, nullable=False)
    catalyst_temperature_b1_s2 = db.Column(db.String, nullable=False)
    ambient_air_temperature = db.Column(db.String, nullable=False)
    time_stamp = db.Column(db.String, nullable=False)
    latitude = db.Column(db.String, nullable=False)
    longitude = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('files', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/dashboard')
@login_required
# def dashboard():
#     user = User.query.filter_by(id=current_user.id).first()
#     return render_template('dashboard.html', user=user)
def dashboard():
    # user_id = current_user.id()
    form = UploadForm()
    user = User.query.filter_by(id=current_user.id).first()
    name = user.name
    if not user:
        return render_template('login.html', user=user, form=form, df="None", name=name)

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    files = glob.glob(os.path.join(user_folder, '*.csv'))
    # Check if there are any files in the UPLOAD_FOLDER directory
    if not files:
        return render_template('dashboard.html', user=user, form=form, df="None", name=name)
    else:

        # Create a pandas DataFrame from the first uploaded CSV file (assuming there is only one)
        # csv_path = os.path.join(app.config['UPLOAD_FOLDER'], files[0])
        df = "123"

        return render_template('dashboard.html', user=user, form=form, df=df, name=name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                token = jwt.encode({'email': user.email, 'exp': datetime.utcnow(
                ) + timedelta(minutes=30)}, app.secret_key)

                return redirect(url_for('dashboard', token=token))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(
                'The email address is already registered. Please choose another one.', 'error')
        else:
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created successfully.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


UPLOAD_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'UPLOAD_FOLDER')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file = form.file.data
        filename = file.filename
        user_folder = os.path.join(
            app.config['UPLOAD_FOLDER'], current_user.name)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        file.save(os.path.join(user_folder, filename))

        # Parse the CSV file and save each row as a Data object

        # with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as csvfile:
        #     csvreader = csv.reader(csvfile)
        #     next(csvreader)  # Skip header row
        #     for row in csvreader:
        #         data = UserFile(bulk_id=row[0], car_reg_no=row[1], vehicle_speed=row[2], heading=row[3], distance=row[4], altitude=row[5], o_s1_b1_voltage=row[6], o_s2_b2_voltage=row[7], o_s1_current=row[8], calculated_engine_load=row[9], engine_rpm=row[10], spark_advance=row[11], absolute_load_value=row[12], throttle_position=row[13], relative_throttle_position=row[14], absolute_throttle_position=row[15], ap_pos_d=row[16], ap_pos_e=row[17], commanded_exhaust_gas_recirculation=row[18], commanded_evaporative_purge=row[19], commanded_throttle_actuator=row[20], fuel_rail_pressure=row[21], o_s1_b1_fuel_air_equivalence_ratio=row[22], fuel_tank_level_input=row[23], o_s1_b1_fuelair_equivalence_ratio=row[24], short_term_fuel_trim_b1=row[25], long_term_fuel_trim_b1=row[26], fuel_air_commanded_equivalence_ratio=row[27], hybrid_battery_pack_remaining=row[28], intake_manifold_absolute_pressure=row[29], mass_air_flow_rate=row[30], egr_error=row[31], absolute_barometric_pressure=row[32], engine_coolant_temperature=row[33], intake_air_temperature=row[34], catalyst_temperature_b1_s1=row[35], catalyst_temperature_b1_s2=row[36], ambient_air_temperature=row[37], time_stamp=row[38], latitude=row[39], longitude=row[40], user_id=current_user)
        #         db.session.add(data)
        #     db.session.commit()

        return redirect(url_for('dashboard'))
    return redirect(url_for('dashboard'))


@app.route('/coolantTemp')
@login_required
def coolantTemp():

    global clicked_trip_number

    clicked_trip_number = None
    bar = plots.coolant_temp()
    return render_template('dashboard.html', plot=bar)


@app.route('/trip_details')
@login_required
# def trip_details():
#     r1 = plots.trip_details()
#     r1 = r1.to_html()
#     return render_template('dashboard.html', plot=r1)
# def trip_details():
#     r1 = plots.trip_details()
#     r1.index.name = 'trip_number'  # Set the index name to 'trip_number'
#     r1 = r1.reset_index()  # Reset the index to convert it into a regular column
#     r1['trip_number'] = r1['trip_number'].apply(
#         lambda x: f'<a href="/trip/{x}">{x}</a>'
#     )
#     r1 = r1.to_html(escape=False)
#     return render_template('dashboard.html', plot=r1)
def trip_details():  # Declare the variable as global

    # def store_trip_number(x):
    #     global clicked_trip_number
    #     clicked_trip_number = x
    #     return f'<a href="/trip/{x}">{x}</a>'
    def store_trip_number(x):
        global clicked_trip_number
        clicked_trip_number = x

<<<<<<< HEAD
        return f'<a href="#" onclick="storeTripNumber({x}); return false;">Plot graph for trip number ==> {x}</a>'
=======
        return f'<a href="#" onclick="storeTripNumber({x}); return false;">{x}</a>'
>>>>>>> fb2786bc7c8186a9e6a65a5141030d8a7c4d04b3

    r1 = plots.trip_details()
    r1.index.name = 'trip_number'  # Set the index name to 'trip_number'
    r1 = r1.reset_index()  # Reset the index to convert it into a regular column

    r1['trip_number'] = r1['trip_number'].apply(store_trip_number)
    # plot1 = plots.plot_coolant_vs_time(
    #     trip_number, plots.forgraph, plots.datacleaning())
    global plot1
    if (clicked_trip_number != None):
        try:
            plot1 = plots.plot_coolant_vs_time(trip_number)
            plot2 = plots.plot_speed_vs_time(trip_number)

        except:
            plot1 = plots.plot_coolant_vs_time(clicked_trip_number)
            plot2 = plots.plot_speed_vs_time(clicked_trip_number)

    r1 = r1.to_html(escape=False)
    return render_template('dashboard.html', plot=r1, clicked_trip_number=clicked_trip_number, plot1=plot1, plot2=plot2)


plot1 = None
plot2 = None
r1 = None
clicked_trip_number = None
trip_number = None


@app.route('/store_trip_number', methods=['POST'])
def store_trip_number():
    data = request.get_json()
    global trip_number
    trip_number = data.get('tripNumber')
    session['clicked_trip_number'] = trip_number
    print(trip_number)
    redirect(url_for('trip_details'))
    return render_template('dashboard.html', plot=r1, clicked_trip_number=clicked_trip_number, plot1=plot1, plot2=plot2)


@app.route('/acc_detect')
@login_required
def acc_detect():

    global clicked_trip_number

    clicked_trip_number = None
    r2 = plots.acc_detect()
    return render_template('dashboard.html', plot=r2)


@app.route('/fuel_consumption_per_trip')
@login_required
def fuel_consumption_per_trip():

    global clicked_trip_number

    clicked_trip_number = None
    r2 = plots.fuel_consumption_per_trip()
    r2 = r2.to_html()
    return render_template('dashboard.html', plot=r2)


@app.route('/delete_csv')
@login_required
def delete_csv():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)
    if len(files) == 1:
        os.remove(os.path.join(user_folder, files[0]))
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
