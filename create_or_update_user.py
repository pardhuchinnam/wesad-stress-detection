from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    username = 'pardhu'
    new_password = 'your_new_pass'

    user = User.query.filter_by(username=username).first()
    if user:
        user.password_hash = generate_password_hash(new_password)
        print(f"Password for user '{username}' reset.")
    else:
        user = User(username=username, email='pardhu@example.com')
        user.password_hash = generate_password_hash(new_password)
        db.session.add(user)
        print(f"User '{username}' created with password.")

    db.session.commit()
