from flask import Flask, request,flash, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import json


app = Flask(__name__)

app.config['MYSQL_HOST'] = "remotemysql.com"
app.config['MYSQL_USER'] = "6bsvenUfKK"
app.config['MYSQL_PASSWORD'] = "SSQ4wN6jYY"
app.config['MYSQL_DB'] = "6bsvenUfKK"
app.secret_key = 'a'
mysql = MySQL(app)
@app.route('/')
def home():
    return render_template("index.html")
@app.route('/log')
def log():
    return render_template("login.html")
@app.route('/login', methods= ["POST"])
def login():
    msg = ''
    if request.method == 'POST' :
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = % s AND password = % s', (username, password ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['userid'] = account['userid']
            session['username'] = account['username']
            session['email'] = account['email']
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect username / Password !")
        
    return render_template('login.html')
@app.route('/reg')
def reg():
    return render_template("register.html")
@app.route('/register', methods = ["POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = % s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'username must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO users VALUES(NULL, %s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            cursor.execute('SELECT userid FROM users WHERE username = % s',(username,))
            accountnew = cursor.fetchone()
            userid = accountnew[0]
            session['userid'] = accountnew[0]
            mysql.connection.commit()
            cursor.execute('INSERT INTO userinfo(userid, username, email) VALUES(% s, % s, % s)', (userid, username, email))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template("register.html", msg = msg)
@app.route('/AddExpense')
def addexpense():
    if 'loggedin' in session:
        return render_template("addexpense.html", username = session['username'])
    return redirect(url_for('log'))
@app.route('/UpdateExpense', methods = ["POST"])
def updateexpense():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST' :
            amount = request.form['amount']
            category = request.form['category']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            userid= session['userid']
            cursor.execute('INSERT INTO expense(userid, username, email, category, amount)  VALUES(% s, % s, % s, %s, % s)', (session['userid'], session['username'], session['email'], category, amount))
            mysql.connection.commit()
            cursor.execute('SELECT limitrem FROM userinfo WHERE userid = % s', (session['userid'],))
            accountexpense = cursor.fetchone()
            limit = accountexpense['limitrem']
            update_rem = int(limit) - int(amount)
            cursor.execute('UPDATE userinfo SET limitrem = % s WHERE userid = % s', (update_rem,session['userid']))
            mysql.connection.commit()
            
            cursor.execute('SELECT limitrem FROM userinfo WHERE userid = % s', (session['userid'],))
            remlimitnew = cursor.fetchone()
            remlimit = remlimitnew['limitrem']
            if remlimit == 0:
                username = session['username']
                email = session['email']
                message = Mail(
                from_email='snehamuthukumar3@gmail.com',
                to_emails=email ,
                subject='Personal Expense Tracker - Expense Alert',
                html_content='Hello '+username + ',\n\n'+ """\n\nThank you for using Personal Expense Tracker.\nPlease do have control on your expenditure, as you have reached your limit. """)

                sg = SendGridAPIClient('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')
                response = sg.send(message)
                cursor.execute('SELECT notifications FROM userinfo WHERE userid = % s', (session['userid'],))
                notification = cursor.fetchone()
                notification_no = notification['notifications']
                notification_no = notification_no + 1
                cursor.execute('UPDATE userinfo SET notifications = % s WHERE userid = % s', (notification_no, session['userid']))
                mysql.connection.commit()
            elif remlimit < 0:
                username = session['username']
                email = session['email']
                message = Mail(
                from_email='snehamuthukumar3@gmail.com',
                to_emails=email ,
                subject='Personal Expense Tracker - Expense Alert',
                html_content='Hello '+username + ',\n\n'+ """\n\nThank you for using Personal Expense Tracker.\nPlease do have control on your expenditure, as you have exceeded your limit. """)
                sg = SendGridAPIClient('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')
                response = sg.send(message)
                cursor.execute('SELECT notifications FROM userinfo WHERE userid = % s', (session['userid'],))
                notification = cursor.fetchone()
                notification_no = notification['notifications']
                notification_no += 1
                cursor.execute('UPDATE userinfo SET notifications = % s WHERE userid = % s', (notification_no, session['userid']))
                mysql.connection.commit()
            msg = "Expense added Successfully !!"
        else:
            msg = "Something went wrong. Please try again later"
        return render_template("addexpense.html", msg = msg, username= session['username'])
    return redirect(url_for('log'))
@app.route('/Profile')
def profileinfo():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM userinfo WHERE userid = % s', (session['userid'],))
        account = cursor.fetchone()
        msg3 = account['notifications']
        limit = account['limitset']
        limitrem = account['limitrem']
        msg4 = int(limit) - int(limitrem)
        

        cursor.execute('SELECT limitset from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg5 = int(account['limitset'])
        cursor.execute('SELECT limitrem from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg7 = int(account['limitrem'])
        msg6 = msg5-msg7

        cursor.execute('SELECT SUM(amount) as tot FROM expense where username = % s', (session['username'],))
        account = cursor.fetchone()
        msg8 = int(account['tot'])
        return render_template('profile.html',msg3 = msg3, msg4 = msg4, username=session['username'], msg1 = session['username'], msg2 = session['email'], msg5= msg5, msg6= msg6, msg7= msg7, msg8=msg8 )
    return redirect(url_for('log'))
@app.route('/SetLimit')
def setlimit():
    if 'loggedin' in session:
        return render_template("setlimit.html", username = session['username'])
    return redirect(url_for('log'))
@app.route('/SetLastMonthLimit')
def setlastmonthlimit():
    if 'loggedin' in session:
        return render_template("setlastmonthlimit.html", username = session['username'])
    return redirect(url_for('log'))
@app.route('/UpdateLimit', methods = ["POST"])
def updatelimit():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST' :
            limit = request.form['limit']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE userinfo SET limitset = % s, limitrem = % s WHERE userid= % s', (limit,limit, session['userid']))
            mysql.connection.commit()
            msg = "Limit for expenses updated Successfully !!"
        else:
            msg = "Something went wrong. Please try again later"
        return render_template("setlimit.html", msg = msg, username= session['username'])
    return redirect(url_for('log'))
@app.route('/UpdatewithExistingLimit', methods = ['POST'])
def updatewithexistinglimit():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT limitset FROM userinfo WHERE username = % s',(session['username'],))
            account = cursor.fetchone()
            limit = account['limitset']
            cursor.execute('UPDATE userinfo SET limitrem = % s WHERE username = % s', (limit, session['username']))
            mysql.connection.commit()
            msg = "Limit for expenses updated Successfully !!"
        else:
            msg = "Something went wrong. Please try again later"
        return render_template("setlastmonthlimit.html", msg = msg, username= session['username'])
    return redirect(url_for('log'))
@app.route('/Dashboard')
def dashboard():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT COUNT(*) as tot FROM users')
        account = cursor.fetchone()
        msg7 = int(account['tot'])
        cursor.execute('SELECT SUM(notifications) as tot FROM userinfo')
        account = cursor.fetchone()
        msg6 = int(account['tot'])
        cursor.execute('SELECT COUNT(*) as tot FROM expense')
        account = cursor.fetchone()
        msg5 = int(account['tot'])
        cursor.execute('SELECT SUM(amount) as tot FROM expense')
        account = cursor.fetchone()
        msg8 = int(account['tot'])
        cursor.execute('SELECT limitset from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg11 = int(account['limitset'])
        cursor.execute('SELECT limitrem from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg33 = int(account['limitrem'])
        msg22 = msg11-msg33
        cursor.execute('SELECT notifications from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg44 = int(account['notifications'])
        user = session['username']
        

        return render_template('dashboard.html', username=session['username'], msg5 = msg5, msg6 = msg6, msg7 = msg7, msg8 = msg8, msg11 = msg11, msg22 = msg22, msg33 = msg33, msg44 = msg44)

    return redirect(url_for('log'))
@app.route('/AllExpenses')
def allexpenses():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT category, amount, timestamp FROM expense WHERE username = % s',(session['username'],))
        data = cursor.fetchall()
        return render_template('allexpenses.html', expenses = data, username = session['username'])
    return redirect(url_for('log'))
@app.route('/ReviewExpenses')
def reviewexpenses():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT category, amount, timestamp FROM expense WHERE username = % s AND YEAR(timestamp) = YEAR(CURRENT_DATE()) AND MONTH(timestamp) = MONTH(CURRENT_DATE())',(session['username'],))
        data = cursor.fetchall()
        return render_template('reviewexpenses.html', expenses = data, username = session['username'])
    return redirect(url_for('log'))
@app.route('/ExpensesThisWeek')
def expensesthisweek():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT category, amount, timestamp FROM expense WHERE username = % s AND DATE(timestamp) BETWEEN DATE_SUB(NOW(), INTERVAL 1 WEEK) AND NOW()',(session['username'],))
        data = cursor.fetchall()
        return render_template('expensesthisweek.html', expenses = data, username = session['username'])
    return redirect(url_for('log'))
@app.route('/Logout')
def logout():
   session.pop('loggedin', None)
   session.pop('userid', None)
   session.pop('username', None)
   session.pop('email', None)
   flash("Successfully Logged Out!!")
   return redirect(url_for('log'))


@app.route('/analysis')
def analysis():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT limitrem from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg33 = int(account['limitrem'])
    
        

        cursor.execute('SELECT limitset from userinfo WHERE username  = % s',(session['username'],))
        account = cursor.fetchone()
        msg11 = int(account['limitset'])

        msg22 = msg11-msg33
        if msg33 <0 :
            msg33=0 
        income_expense = []
        income_expense.append(msg33)
        income_expense.append(msg22)


        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute('SELECT timestamp FROM expense WHERE username = % s',(session['username'],))
        dates = cursor.fetchall()
        cursor.close()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT amount FROM expense WHERE username = % s',(session['username'],))
        expenses= cursor.fetchall()
        
        cursor.close()
        expenses_done = []
        for expense_amount in expenses:
            expenses_done.append(expense_amount['amount'])
        dates_label = []

        for dateval in dates:
            dates_label.append(str(dateval['timestamp']))

        return render_template('chart.html',income_vs_expense=json.dumps(income_expense), expenses_done=json.dumps(expenses_done),
                                dates_label =json.dumps(dates_label), username = session['username'])
    return redirect(url_for('log'))


if __name__ == '__main__':
    app.run(debug = True, host ="0.0.0.0", port = 8080)