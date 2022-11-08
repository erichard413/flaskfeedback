"""seed file to create tables"""

from models import db, User
from app import app

db.drop_all()
db.create_all()

username='admin'
password='admin'
email='erik@erikrichard.com'
first='Erik'
last='Richard'
is_admin=True

admin_user = User.register(username, password, email, first, last, is_admin)
db.session.add(admin_user)
db.session.commit()