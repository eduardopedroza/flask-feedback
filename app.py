from flask import Flask, render_template, redirect, session, flash
from models import db, connect_db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, UpdateFeedbackForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback_ex'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

app.app_context().push()

connect_db(app)
db.create_all()

app.config['SECRET_KEY'] = "SECRET!"


@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User.register(
            username = form.username.data,
            password = form.password.data,
            )
        
        new_user.email = form.email.data,
        new_user.first_name = form.first_name.data,
        new_user.last_name = form.last_name.data
        
        db.session.add(new_user)
        db.session.commit()

        session['user_username'] = new_user.username

        return redirect(f'/users/{new_user.username}')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            session['user_username'] = user.username
            return redirect('/secret')
        else:
            flash('Incorrect username/password')
    
    return render_template('login.html', form=form)

@app.route('/users/<username>')
def show_user(username):

    if 'user_username' not in session:
        flash("You must be logged in to view this page")
        return redirect('/login')

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found")
        return redirect('/')
    
    user_info = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

    feedbacks = Feedback.query.filter_by(username=username).all()

    return render_template('user_info.html', user=user_info, feedbacks=feedbacks)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):

    if 'user_username' not in session or session['user_username'] != username:
        flash("You do not have permission to delete this user.")
        return redirect(f'/users/{username}')
    
    user = User.query.get_or_404(username)

    Feedback.query.filter_by(username=username).delete()

    db.session.delete(user)
    db.session.commit()

    session.clear()

    return redirect('/')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def show_and_add_feedback(username):

    if 'user_username' not in session or session['user_username'] != username:
        flash("You must be logged in to add feedback.")
        return redirect('/login')
        
    form = FeedbackForm()

    if form.validate_on_submit():
        new_feedback = Feedback(
            title = form.title.data,
            content = form.content.data,
            username = username
        )

        db.session.add(new_feedback)
        db.session.commit()

        return redirect(f'/users/{username}')
    
    return render_template('feedback_form.html', form=form)

@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def show_and_update_feedback(feedback_id):

    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.username

    if 'user_username' not in session or session['user_username'] != username:
        flash("You must be logged in to add feedback.")
        return redirect('/login')
    
    form = UpdateFeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        
        return redirect(f'users/{username}')

    return render_template('feedback_update_form.html', form=form)
    
@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):

    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.username

    if 'user_username' not in session or session['user_username'] != username:
        flash("You must be logged in to add feedback.")
        return redirect('/login')
    
    db.session.delete(feedback)
    db.session.commit()

    return redirect(f'/users/{username}')

    

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

