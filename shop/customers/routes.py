from flask import render_template, session, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_required, current_user, logout_user, login_user
from shop import app, db, photos, search, bcrypt, login_manager
from .forms import CustomerRegisterForm, CustomerLoginFrom
from .model import Register, CustomerOrder

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.trainers import ListTrainer

import secrets
import os
import json
import pdfkit
import stripe

with open('shop/data/file.txt', 'r') as file:
    conversation = file.read()

bot = ChatBot("Van Lang's Resume ChatBot")
trainer = ListTrainer(bot)
trainer.train(["Hey", "Hi there!",
               "Hi", "Hi!",
               "How are you doing?", "I'm doing great.",
               "That is good to hear", "Thank you.",
               "You're welcome.",
               "What is your name?", "My name is Van Lang ChatBot",
               "Who created you?", "Mr Nhat",
               "What product your shop have?", "We have apple, acer, dell, hp"
               "Tell me about yourself?", "My name is VLL. I am a third year computer engineering student at PVGCOET",
               "Contact", "Email : vanlang@gmail.com, Mobile number : +91 9021393816 Location : Pune, Maharashtra",
               "Education?", "Bachelor of Engineering (B.E), Computer Science & Engineering\n Pune Vidyarthi Grihas College Of Engineering And Technology Pune '\n'2018 - 2022 '\n'CGPA: 8.84/10 '\n'Senior Secondary (XII), Science Sir Parashurambhau College Pune Maharashtra (MAHARASHTRA STATE BOARD board) Year of completion: 2018 Percentage: 88.40% Secondary (X) Sant Meera School Aurangabad (MAHARASHTRA STATE BOARF board) Year of completion: 2016 Percentage: 96.20%",
               "Tell me about yourself",
               "My name is Nhat Somwase. I am a third year computer engineering student at PVGCOET",
               "Contact",
               "Email : sunandasomwase@gmail.com, Mobile number : +91 9021393816 Location : Pune, Maharashtra",
               "Projects",
               "Dont Known"
               ])
trainer = ChatterBotCorpusTrainer(bot)
trainer.train("chatterbot.corpus.english")

buplishable_key = 'pk_test_MaILxTYQ15v5Uhd6NKI9wPdD00qdL0QZSl'
stripe.api_key = 'sk_test_9JlhVB6qwjcRdYzizjdwgIo0Dt00N55uxbWy'


@app.route('/payment', methods=['POST'])
def payment():
    invoice = request.get('invoice')
    amount = request.form.get('amount')
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )
    charge = stripe.Charge.create(
        customer=customer.id,
        description='Myshop',
        amount=amount,
        currency='usd',
    )
    orders = CustomerOrder.query.filter_by(customer_id=current_user.id, invoice=invoice).order_by(
        CustomerOrder.id.desc()).first()
    orders.status = 'Paid'
    db.session.commit()
    return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    return render_template('customer/thank.html')


@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        register = Register(name=form.name.data, username=form.username.data, email=form.email.data,
                            password=hash_password, country=form.country.data, city=form.city.data,
                            contact=form.contact.data, address=form.address.data, zipcode=form.zipcode.data)
        db.session.add(register)
        flash(f'Welcome {form.name.data} Thank you for registering', 'success')
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('customer/register.html', form=form)


@app.route('/customer/login', methods=['GET', 'POST'])
def customerLogin():
    form = CustomerLoginFrom()
    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('You are login now!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('home'))
            # return render_template('customer/profile.html', img=user.profile)
        flash('Incorrect email and password', 'danger')
        return redirect(url_for('customerLogin'))

    return render_template('customer/login.html', form=form)


@app.route(
    '/profile_customer/<id>/<name>/<username>/<email>/<city>/<contact>/<address>/<zipcode>/<profile>/<date_created>')
def profile_customer(id, name, username, email, city, contact, address, zipcode, profile, date_created):
    a = []
    b = []
    a.extend(["Name", "Username", "Email", "City", "Contact", "Address", "Zipcode", "Date_created"])
    b.append([name, username, email, city, contact, address, zipcode, date_created])
    return render_template('profile.html', a=a, b=b, img=profile, username=username)


@app.route('/customer/logout')
def customer_logout():
    logout_user()
    return redirect(url_for('home'))


def updateshoppingcart():
    for key, shopping in session['Shoppingcart'].items():
        session.modified = True
        del shopping['image']
        del shopping['colors']
    return updateshoppingcart


@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        updateshoppingcart()
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id, orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been sent successfully', 'success')
            return redirect(url_for('orders', invoice=invoice))
        except Exception as e:
            print(e)
            flash('Some thing went wrong while get order', 'danger')
            return redirect(url_for('getCart'))


@app.route('/orders/<invoice>')
@login_required
def orders(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(
            CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount'] / 100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f" % (1.06 * float(subTotal)))

    else:
        return redirect(url_for('customerLogin'))
    return render_template('customer/order.html', invoice=invoice, tax=tax, subTotal=subTotal, grandTotal=grandTotal,
                           customer=customer, orders=orders)


@app.route('/get_pdf/<invoice>', methods=['POST'])
@login_required
def get_pdf(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        if request.method == "POST":
            customer = Register.query.filter_by(id=customer_id).first()
            orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(
                CustomerOrder.id.desc()).first()
            for _key, product in orders.orders.items():
                discount = (product['discount'] / 100) * float(product['price'])
                subTotal += float(product['price']) * int(product['quantity'])
                subTotal -= discount
                tax = ("%.2f" % (.06 * float(subTotal)))
                grandTotal = float("%.2f" % (1.06 * subTotal))

            rendered = render_template('customer/pdf.html', invoice=invoice, tax=tax, grandTotal=grandTotal,
                                       customer=customer, orders=orders)
            pdf = pdfkit.from_string(rendered, False)
            response = make_response(pdf)
            response.headers['content-Type'] = 'application/pdf'
            response.headers['content-Disposition'] = 'inline; filename=' + invoice + '.pdf'
            return response
    return request(url_for('orders'))


@app.route('/chat')
def homie():
    return render_template('chatbot.html')


@app.route('/get')
def get_bot_response():
    txt = request.args.get('msg')
    return str(bot.get_response(txt))
