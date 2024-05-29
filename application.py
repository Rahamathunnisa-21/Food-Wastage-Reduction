from flask import Flask,redirect,url_for,render_template,request,flash,abort,session,send_file
from flask_session import Session
from key import secret_key,salt1,salt2
import flask_excel as excel
from stoken import token
from cmail import sendmail
from datetime import date,timedelta
#from flaskext.mysql import MySQL
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
import mysql.connector
from io import BytesIO
import os
app=Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
Session(app)
excel.init_excel(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='babitha',db='prm')
'''db= os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute('create table if not exists users(username varchar(15) primary key,password varchar(15),email varchar(80),email_status enum("confirmed","not confirmed"))')
    cursor.execute('CREATE TABLE if not exists donations(id INT PRIMARY KEY AUTO_INCREMENT,food_type VARCHAR(100) NOT NULL,quantity INT NOT NULL,expiration_date DATE NOT NULL,handling_instructions VARCHAR(255))')
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db)'''    
@app.route('/')
def index():
    return render_template('title.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
            p_count=cursor.fetchone()[0]
            if p_count==1:
                session['user']=username
                cursor.execute('select email_status from users where username=%s',[username])
                status=cursor.fetchone()[0]
                cursor.close()
                if status!='confirmed':
                    return redirect(url_for('inactive'))
                else:
                    return redirect(url_for('home'))  
            else:
                cursor.close()
                flash('invalid password')
                return render_template('login.html')
        else:
            cursor.close()
            flash('invalid username')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/inactive')
def inactive():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            return redirect(url_for('home'))
        else:
            return render_template('inactive.html')
    else:
        return redirect(url_for('login'))
@app.route('/homepage',methods=['GET','POST'])
def home():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            return render_template('homepages.html')
        else:
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))
@app.route('/take a look!',methods=['GET','POST'])
def take():
        return render_template('foodreduce.html')        
@app.route('/resendconfirmation')
def resend():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.execute('select email from users where username=%s',[username])
        email=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('home'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email,salt1),_external=True)
            body=f"Please confirm your mail-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))
@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        try:
            cursor.execute('insert into users (username,password,email) values(%s,%s,%s)',(username,password,email))
        except mysql.connector.IntegrityError:
            flash('Username or email is already in use')
            return render_template('registration.html')
        else:
            mydb.commit()
            cursor.close()
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email,salt1),_external=True)
            body=f"Thanks for Registering food Wastage Reduction.Follow this link-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return render_template('login.html')
    return render_template('registration.html')
    
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt1,max_age=120)
    except Exception as e:
        #print(e)
        abort(404,'Link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where email=%s',[email])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('login'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update users set email_status='confirmed' where email=%s",[email])
            mydb.commit()
            flash('Email confirmation success')
            return redirect(url_for('login'))
@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT email_status from users where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status!='confirmed':
                flash('Please Confirm your email first')
                return render_template('forgot.html')
            else:
                subject='Forget Password'
                confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
                body=f"Use this link to reset your password-\n\n{confirm_link}"
                sendmail(to=email,body=body,subject=subject)
                flash('Reset link sent check your email')
                return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')
@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')  
@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        location = request.form["location"]
        food_type = request.form["food_type"]
        quantity = request.form["quantity"]
        expiration_date = request.form["expiration_date"]
        handling_instructions = request.form["handling_instructions"]

        cur = mydb.cursor()
        cur.execute("INSERT INTO donations (food_type, quantity, expiration_date, handling_instructions,location) VALUES (%s, %s, %s, %s,%s)",
                    (food_type, quantity, expiration_date, handling_instructions,location))
        mydb.commit()
        cur.close()
        return render_template("thank.html")
    return render_template("donate.html")        
@app.route('/inventory')
def inventory():
    '''if request.method=='POST':
    expired=request.form['expiration_date']'''
    # Retrieve food items from the database
    cur = mydb.cursor()
    cur.execute("SELECT DISTINCT food_type, quantity, expiration_date,handling_instructions,location FROM donations")
    donations = cur.fetchall()
    '''cur.execute("SELECT  expiration_date FROM donations")
    expiration_date=cur.fetchall()
    today = date.today()'''
    query = "SELECT food_type, quantity, expiration_date,handling_instructions FROM donations WHERE expiration_date < CURDATE()"
    cur.execute(query)
    expiring_items = cur.fetchall()
    query = "SELECT food_type, quantity, expiration_date,handling_instructions FROM donations WHERE quantity <=0"
    cur.execute(query)
    quality = cur.fetchall()
    query = "SELECT  DISTINCT food_type, quantity, expiration_date,handling_instructions FROM donations WHERE expiration_date <= CURDATE() + INTERVAL 3 DAY"
    cur= mydb.cursor()
    cur.execute(query)
    nearing_expiration_items = cur.fetchall()
    cur.close()
    return render_template('inventory.html',donations=donations,expiring_items=expiring_items,quality=quality,nearing_expiration_items=nearing_expiration_items)
@app.route("/user", methods=["GET", "POST"])
def user():
    '''if request.method == "POST":
    location = request.form["location"]
        food_type = request.form["food_type"]
        quantity = request.form["quantity"]
        expiration_date = request.form["expiration_date"]
    handling_instructions = request.form["handling_instructions"]'''
    cur = mydb.cursor()
    cur.execute("SELECT DISTINCT food_type, quantity, expiration_date,handling_instructions,location FROM donations")
    donations = cur.fetchall()   
    cur.close()
    return render_template('food.html',donations=donations)

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
if __name__=="__main__":       
    app.run(debug=True,use_reloader=True)