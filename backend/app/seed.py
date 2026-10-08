"""Populate demo data:  python -m app.seed   (run from backend/)"""
import random
from datetime import timedelta

from .database import Base, engine, SessionLocal
from .models import User, Item, Transaction, utcnow

random.seed(7)
ITEMS = [("Arduino Uno", "Microcontroller", 12), ("Raspberry Pi 4", "Microcontroller", 8),
         ("ESP32 Board", "Microcontroller", 15), ("Ultrasonic Sensor", "Sensor", 20),
         ("DHT11 Sensor", "Sensor", 25), ("Breadboard", "Accessory", 30), ("Multimeter", "Tool", 6)]
USERS = [("Aayush Sankhla", "aayush@example.com", "admin"), ("Aryan Singh", "aryan@example.com", "member"),
         ("Isha Agrawal", "isha@example.com", "member"), ("Manish Sain", "manish@example.com", "member")]


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    users = [User(name=n, email=e, role=r) for n, e, r in USERS]
    items = [Item(name=n, category=c, qr_code=f"ITM-{i+1:04d}", quantity_total=q, quantity_available=q)
             for i, (n, c, q) in enumerate(ITEMS)]
    db.add_all(users + items); db.commit()
    now = utcnow()
    weights = [10, 7, 6, 5, 4, 2, 1]
    for day in range(30, 0, -1):
        for _ in range(random.randint(1, 5)):
            it, u = random.choices(items, weights)[0], random.choice(users)
            issued = now - timedelta(days=day, hours=random.randint(0, 10))
            returned = issued + timedelta(days=random.randint(1, 6))
            if returned > now:
                if it.quantity_available > 0:
                    it.quantity_available -= 1
                    db.add(Transaction(item_id=it.id, user_id=u.id, issued_at=issued,
                                       due_at=issued + timedelta(days=7), status="issued"))
                continue
            db.add(Transaction(item_id=it.id, user_id=u.id, issued_at=issued, due_at=issued + timedelta(days=7),
                               returned_at=returned, status="returned"))
    db.commit()
    print(f"Seeded {len(users)} users, {len(items)} items, {db.query(Transaction).count()} transactions")
    db.close()


if __name__ == "__main__":
    main()
