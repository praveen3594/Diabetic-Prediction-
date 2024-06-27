from flask import Flask, request, render_template, redirect, session,url_for
import bcrypt
import pickle
import sqlite3
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database1.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)
DATABASE = 'database1.db'

app.secret_key = 'secret_key'

def create_tables():
    conn = sqlite3.connect(DATABASE, isolation_level=None)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user (
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT PRIMARY KEY,
                password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS person (
                person_name TEXT,
                user_age INTEGER,
                pregnancies INTEGER,
                glucose_level REAL,
                blood_pressure REAL,
                skin_thickness REAL,
                insulin REAL,
                bmi REAL,
                diabetes_pedigree_function REAL,
                prediction TEXT)''')
    conn.commit()
    conn.close()

def insert_user(name, age, email, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO user (name, age, email, password) VALUES (?, ?, ?, ?)",
              (name, age, email, password))
    conn.commit()
    conn.close()

def insert_person(person_name, user_age, pregnancies, glucose_level, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, prediction):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO person (person_name, user_age, pregnancies, glucose_level, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, prediction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (person_name, user_age, pregnancies, glucose_level, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, prediction))
    conn.commit()
    conn.close()

def check_user(email, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        return True
    else:
        return False

def get_user_by_email(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_persons():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM person")
    all_persons = c.fetchall()
    conn.close()
    return all_persons

def calculate_dpf3(num_relatives, relationships):
    # Dictionary to store weights for different relationships
    weights = {
        "parent": 0.1,
        "sibling": 0.15,
        "grandparent": 0.02,
        # Add more relationships and their weights as needed
    }

    total_dpf = 0

    for i in range(num_relatives):
        relationship = relationships[i].lower()
        if relationship in weights:
            total_dpf += weights[relationship]

    return total_dpf

@app.route('/')
def index():
    return render_template('Diabetic Prediction/templates/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        age = int(request.form.get('age'))
        email = request.form.get('email')
        password = request.form.get('password')
        if not (name and email and password and age):
            return render_template('Diabetic Prediction/templates/register.html', error='All fields are required.')
        try:
            insert_user(name, age, email, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
            return redirect('/login')
        except:
            return render_template('Diabetic Prediction/templates/register.html', error='An error occurred while registering. Please try again.')
    return render_template('Diabetic Prediction/templates/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if check_user(email, password):
            session['email'] = email
            return redirect('/menu')
        else:
            return render_template('Diabetic Prediction/templates/login.html', error='Invalid user')
    return render_template('Diabetic Prediction/templates/login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        if name == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return redirect('/details')
        else:
            return render_template('Diabetic Prediction/templates/admin.html', error='Invalid user')
    return render_template('Diabetic Prediction/templates/admin.html')

@app.route('/details')
def details():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM person")  # Assuming 'person' is the table name
    data = c.fetchall()
    conn.close()
    return render_template('Diabetic Prediction/templates/result.html', data=data)

@app.route('/menu')
def menu():
    if session['email']:
        return render_template('Diabetic Prediction/templates/menu.html')
    
    return redirect('/login')

@app.route('/calculate_dpf', methods=['GET', 'POST'])
def calculate_dpf():
    if request.method == 'POST':
        num_relatives = int(request.form['num_relatives'])
        # Render template with DPF value
        return redirect(url_for('calculate', num_relatives=num_relatives))
    else:
        return render_template('Diabetic Prediction/templates/calculate_dpf.html')

@app.route('/calculate/<int:num_relatives>', methods=['GET', 'POST'])
def calculate(num_relatives):
    if request.method == 'POST':
        relationships = [request.form[f'relationship{i}'] for i in range(1, num_relatives+1)]

        # Calculate DPF
        dpf = calculate_dpf3(num_relatives, relationships)
        return redirect(url_for('dpfresult', dpf=dpf))
    else:
        return render_template('Diabetic Prediction/templates/calculate.html', num_relatives=num_relatives)

@app.route('/dpfresult/<dpf>')
def dpfresult(dpf):
    return render_template('Diabetic Prediction/templates/dpfresult.html', dpf=dpf)

@app.route('/home')
def home():
    if 'email' in session:
        user = get_user_by_email(session['email'])
        return render_template('Diabetic Prediction/templates/home.html', user=user)
    return redirect('/login')

@app.route('/predictdata', methods=['GET','POST'])
def predict_datapoint():
    result=""
    if request.method == 'POST':
        Pregnancies = int(request.form.get("Pregnancies"))
        Glucose = float(request.form.get('Glucose'))
        BloodPressure = float(request.form.get('BloodPressure'))
        SkinThickness = float(request.form.get('SkinThickness'))
        Insulin = float(request.form.get('Insulin'))
        BMI = float(request.form.get('BMI'))
        DiabetesPedigreeFunction = float(request.form.get('DiabetesPedigreeFunction'))
        Age = float(request.form.get('Age'))
        Name = request.form.get('name')
        
        new_data=scaler.transform([[Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction,Age]])
        predict=Diabetic Prediction.model.predict(new_data)
       
        if predict[0] ==1 :
            result = 'Diabetic'
            instructions = [
                "Make and eat healthy food.",
                "Be active most days.",
                "Test your blood sugar often.",
                "Take medicines as prescribed, even if you feel good.",
                "Learn ways to manage stress.",
                "Cope with the emotional side of diabetes.",
                "Go to checkups."
            ]
        else:
            result ='Non-Diabetic'
            instructions = ["Congratulations! Yours healthy habits light up the path to witness,illuminating a future filled with vitality and joy."]
        
        new_person = insert_person(user_age=Age,pregnancies=Pregnancies,
                        glucose_level=Glucose, blood_pressure=BloodPressure,
                        skin_thickness=SkinThickness, insulin=Insulin, bmi=BMI,
                        diabetes_pedigree_function=DiabetesPedigreeFunction,
                        prediction=result,person_name=Name)
        conn = sqlite3.connect('database1.db')
        cursor = conn.cursor()
            
        return render_template('Diabetic Prediction/templatessingle_prediction.html',result=result,instructions=instructions)

    else: 
        return render_template('Diabetic Prediction/templateshome.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    create_tables()
    scaler = pickle.load(open("Model/standardScalar.pkl", "rb"))
    model = pickle.load(open("Model/modelForPrediction.pkl", "rb"))
    app.run(debug=True, port=7000)
