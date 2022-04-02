from flask import render_template, session, request, redirect, url_for, flash
from shop import app, db, bcrypt
from .forms import RegistrationForm, LoginForm
from .models import User
from shop.products.models import Addproduct, Category, Brand
from shop.customers.model import Register


@app.route('/admin')
def admin():
    products = Addproduct.query.all()
    return render_template('admin/index.html', title='Admin page', products=products)


@app.route('/brands')
def brands():
    brands = Brand.query.order_by(Brand.id.desc()).all()
    return render_template('admin/brand.html', title='brands', brands=brands)


@app.route('/categories')
def categories():
    categories = Category.query.order_by(Category.id.desc()).all()
    return render_template('admin/brand.html', title='categories', categories=categories)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = User(name=form.name.data, username=form.username.data, email=form.email.data,
                    password=hash_password)
        db.session.add(user)
        flash(f'welcome {form.name.data} Thanks for registering', 'success')
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('admin/register.html', title='Register user', form=form)


role = "normal"


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        global role
        if role == "normal" or role != "normal":
            role = user.name
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['email'] = form.email.data
            flash(f'welcome {user.username} you are loged in now', 'success')
            return redirect(url_for('admin'))
        else:
            flash(f'Wrong email and password', 'success')
            return redirect(url_for('login'))
    return render_template('admin/login.html', title='Login page', form=form)


@app.route('/profile')
def profile():
    users = User.query.all()
    return render_template('admin_profile.html', users=users)


@app.route('/profile/<int:id>')
def view_profile(id):
    user = User.query.get_or_404(id)
    print(role)
    a = []
    b = []
    a.extend(["name", "user_name", "email"])
    b.extend([user.name, user.username, user.email])
    return render_template('view_profile.html', user=user, a=a, b=b, role=role)


@app.route('/profile/edit/<int:id>')
def editProfile(id):
    user = User.query.get_or_404(id)
    return render_template('edit_profile_admin.html', user=user)


@app.route('/profile/edit/<int:id>/Edit_Action', methods=['GET', 'POST'])
def edit_Admin_Profile(id):
    user = User.query.get_or_404(id)
    name = request.form['name']
    username = request.form['username']
    email = request.form['email']
    password = bcrypt.generate_password_hash(request.form['password'])
    image = request.form['image']

    user.name = name
    user.username = username
    user.email = email
    user.password = password
    user.profile = image
    # update the db
    db.session.add(user)
    db.session.commit()
    flash(f'Update success', 'success')
    return render_template('edit_profile_admin.html', user=user)


@app.route('/profile/delete/<int:id>')
def delete_User(id):
    user_del = User.query.get_or_404(id)
    try:
        db.session.delete(user_del)
        db.session.commit()
        # shot the message
        flash("Deleted successfully")
        # show all post after del
        user = User.query.order_by(User.id)
        return redirect(url_for("profile"))
    except:
        # catch the except ok
        flash("Error while delete!!!")


@app.route('/customer_profile')
def showCustomerProfile():
    users = Register.query.all()
    return render_template('customer_profile.html', users=users)
