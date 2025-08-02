from app import db, bcrypt, User

admin_email = "admin@example.com"
admin_password = bcrypt.generate_password_hash("Admin123").decode('utf-8')

admin = User(name="System Admin", email=admin_email, password=admin_password, role="admin")
db.session.add(admin)
db.session.commit()

print("Admin user created.")
