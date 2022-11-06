from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, LogInForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "pugsrcool24"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    """takes user to home page"""
    fbk = Feedback.query.all()
    if session['curruser']:
        user = User.query.get_or_404(session['curruser'])
    else:
        user = None;
    return render_template('index.html', fbk=fbk, user=user)
    

@app.route('/register', methods=["GET","POST"])
def register_user():
    """GET: show registration form/POST: process registration & add new user"""
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first = form.first_name.data
        last = form.last_name.data
        new_user = User.register(username, password, email, first, last)
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another.')
            return render_template("register.html", form=form)
        session["curruser"] = new_user.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f'/users/{new_user.username}')
    return render_template('register.html', form=form)

@app.route('/login', methods=["GET","POST"])
def log_in():
    """GET: shows log in page POST: logs user in"""
    form = LogInForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f'Welcome back, {user.username}.', "success")
            session['curruser'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ["Invalid username/password."]
    return render_template("login.html", form=form)

@app.route('/users/<username>')
def secret_page(username):
    """Shhh... secret"""
    if session['curruser']:
        user = User.query.get_or_404(username)
        fbk = user.fbk
        return render_template("user.html", user=user, fbk=fbk)
    else:
        flash('Please log in first!', "danger")
        return redirect('/login')

@app.route('/logout')
def log_out():
    """Log out user"""
    if session['curruser']:
        session['curruser'] = None
    return redirect('/')
@app.route('/feedback/<int:f_id>/update', methods=["GET","POST"])
def update_feedback(f_id):
    """GET: show update form POST: update info from form"""
    fbk = Feedback.query.get_or_404(f_id)
    form = FeedbackForm(obj=fbk)
    
    if form.validate_on_submit():
        fbk.title = form.title.data
        fbk.content = form.content.data
        db.session.add(fbk)
        db.session.commit()
        flash("Feedback updated successfully!", "success")
        return redirect(f'/users/{fbk.users.username}')
    else:
        return render_template('update.html', form=form, fbk=fbk)
@app.route('/feedback/<int:f_id>/delete', methods=["POST","GET"])
def delete_feedback(f_id):
    """This will delete feedback and redirect user"""
    fbk = Feedback.query.get_or_404(f_id)
    user = fbk.users.username
    if (session['curruser'] == user or user.is_admin):
        
        db.session.delete(fbk)
        db.session.commit()
        flash("Feedback deleted successfully!", "success")
        if user.is_admin:
            return redirect('/')
        return redirect(f'/users/{user}')
    else:
        flash("You do not have permission to do that!", "danger")
        return redirect('/')
@app.route('/users/<username>/feedback/add', methods=["POST","GET"])
def add_feedback(username):
    """GET: shows feedback form POST: Add feedback to database & display user page"""
    if session['curruser']:
        form = FeedbackForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data

            new_fbk = Feedback(title=title, content=content, username=username)
            db.session.add(new_fbk)
            db.session.commit()
            flash("Feedback added successfully!", "success")
            return redirect(f'/users/{username}')
        else:
            return render_template("add.html", form=form)
    else:
        flash("You've got to log in first!", "danger")
        return redirect('/login')
@app.route('/users')
def show_users():
    """Show all users"""
    user = User.query.get_or_404(session['curruser'])
    users=User.query.all()
    return render_template("users.html", users=users, user=user)
@app.errorhandler(404)
def not_found_err(e):
    """displays when 404'd"""
    fbk = Feedback.query.all()
    flash("404 - File not found!", "danger")
    return render_template("404.html", fbk=fbk)
@app.errorhandler(404)
def not_authenticated_err(e):
    """displays when 401'd"""
    fbk = Feedback.query.all()
    flash("401 - User not authenticated!", "danger")
    return render_template("404.html", fbk=fbk)
@app.route('/users/makeadmin', methods=["GET","POST"])
def make_admin_page():
    """to make an admin"""
    u = User.query.get(session['curruser'])
    if u.is_admin:
        form = UserForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            email = form.email.data
            first = form.first_name.data
            last = form.last_name.data
            is_admin = True
            new_user = User.register(username, password, email, first, last, is_admin)
            try:
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                form.username.errors.append('Username taken. Please pick another.')
                return render_template("register.html", form=form)
            flash(f'Admin account {username} created.', "success")
            return redirect(f'/')
        return render_template('register.html', form=form)
    else:
        flash("You do not have permission to access that page!", "danger")
        return redirect("/")
@app.route('/users/<username>/delete', methods=["POST"])
def delete_user(username):
    curr_user = User.query.get_or_404(session['curruser'])
    if curr_user.is_admin:

        user = User.query.get_or_404(username)
        flash(f"User {user.username} deleted!", "success")
        db.session.delete(user)
        db.session.commit()

        return redirect('/users')
    else:
        flash('You do not have permissions to do that!', "danger")
        return redirect('/')
    
    