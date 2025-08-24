from main import create_app
from models import db, User, Sales, UserRole
from datetime import datetime
import random

app = create_app()
app.app_context().push()

# Temsilcileri al
reps = User.query.filter_by(role=UserRole.REPRESENTATIVE).all()
print(f'Found {len(reps)} representatives')

# Her temsilci için örnek satış verileri ekle
for rep in reps[:5]:  # İlk 5 temsilci için
    for i in range(random.randint(1, 3)):  # Her temsilci için 1-3 satış
        sale = Sales(
            representative_id=rep.id,
            date=datetime.now().date(),
            product_group=random.choice(['Elektronik', 'Bilgisayar', 'Telefon', 'Tablet']),
            brand=random.choice(['Samsung', 'Apple', 'Dell', 'HP', 'Lenovo']),
            product_name=f'Product {random.randint(1,100)}',
            quantity=random.randint(1,5),
            unit_price=random.randint(5000,25000),
            total_price=random.randint(5000,25000),
            net_price=random.randint(5000,25000)
        )
        db.session.add(sale)
    
    print(f'Added sales for {rep.username}')

db.session.commit()
print('Sample sales data created successfully') 