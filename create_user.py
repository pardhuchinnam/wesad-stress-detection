from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    username = 'testuser'
    password = 'testpassword'

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User {username} already exists.")
    else:
        user = User(username=username, email='testuser@example.com')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created user {username} with password {password}")