import yaml
import os
from sqlalchemy import create_engine, text
from datetime import datetime, timezone, timedelta

# Database connection configuration
def get_engine(db_name, port):
    url = f"postgresql+psycopg2://postgres:postgres@localhost:{port}/{db_name}"
    return create_engine(url)

def seed_all():
    # Get file path for yaml
    base_path = os.path.dirname(__file__)
    yaml_path = os.path.join(base_path, "mock_data.yaml")
    
    if not os.path.exists(yaml_path):
        print(f"❌ Error: {yaml_path} not found.")
        return
        
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # 1. Seed Account Users (user_id IS the unique identifier for both PK and login)
    engine = get_engine("account_db", 5433)
    with engine.connect() as conn:
        for u in data['users']:
            conn.execute(text("DELETE FROM users WHERE user_id = :uid OR username = :uid"), {"uid": u['user_id']})
            conn.execute(text("""
                INSERT INTO users (user_id, username, email, role, registration_status, created_at, updated_at)
                VALUES (:uid, :uid, :email, :role, 'active', NOW(), NOW())
            """), {"uid": u['user_id'], "email": u['email'], "role": u['role']})
        conn.commit()
    print(f"✅ Seeded {len(data['users'])} Account Users")

    # 2. Seed Events (Ensuring table exists)
    engine = get_engine("event_db", 5432)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                event_id VARCHAR(50) PRIMARY KEY, name VARCHAR(255) NOT NULL, description TEXT NOT NULL,
                location VARCHAR(255) NOT NULL, category VARCHAR(50), guest_allowed BOOLEAN NOT NULL DEFAULT FALSE,
                ticket_limit INTEGER, remaining_tickets INTEGER NOT NULL DEFAULT 0,
                cancellation_deadline TIMESTAMP WITH TIME ZONE, latitude DECIMAL(9,6), longitude DECIMAL(9,6),
                "checkinRadiusMeters" DECIMAL(9,6), event_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                event_end_time TIMESTAMP WITH TIME ZONE NOT NULL, registration_start TIMESTAMP WITH TIME ZONE NOT NULL,
                registration_end TIMESTAMP WITH TIME ZONE NOT NULL, faqs JSONB DEFAULT '[]',
                status INTEGER NOT NULL DEFAULT 0, is_draft BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        conn.execute(text("DELETE FROM events"))
        for ev in data['events']:
            start = datetime.now(timezone.utc) + timedelta(hours=ev['time_offset'])
            end = start + timedelta(hours=ev['duration'])
            reg_start = start + timedelta(days=ev['registration_offset'])
            reg_end = start + timedelta(days=-1)
            cancel = start - timedelta(hours=ev.get('cancellation_offset', 24))
            
            conn.execute(text("""
                INSERT INTO events (event_id, name, description, location, category, event_start_time, event_end_time, 
                                   registration_start, registration_end, cancellation_deadline, status, is_draft, 
                                   latitude, longitude, "checkinRadiusMeters")
                VALUES (:id, :name, 'Mock Description', :loc, :cat, :start, :end, :rs, :re, :cd, :status, FALSE, 
                        :lat, :lon, :radius)
            """), {
                "id": ev['id'], "name": ev['name'], "loc": ev['location'], "cat": ev['category'], 
                "start": start, "end": end, "rs": reg_start, "re": reg_end, "cd": cancel, "status": ev['status'],
                "lat": ev['lat'], "lon": ev['lon'], "radius": ev['radius']
            })
        conn.commit()
    print("✅ Seeded Events")

    # 3. Seed Transactions
    engine = get_engine("transaction_db", 5434)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id VARCHAR PRIMARY KEY, user_id VARCHAR NOT NULL, event_id VARCHAR NOT NULL,
                status VARCHAR NOT NULL, ticket_id VARCHAR, guest_count INTEGER DEFAULT 0,
                diet_type VARCHAR, self_driving BOOLEAN, 
                registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        conn.execute(text("DELETE FROM transactions"))
        for tx in data['transactions']:
            conn.execute(text("""
                INSERT INTO transactions (transaction_id, user_id, event_id, status, ticket_id, guest_count, diet_type, self_driving, registered_at)
                VALUES (:id, :uid, :eid, :status, :tid, 0, 'non-veg', TRUE, NOW())
            """), {"id": tx['id'], "uid": tx['user_id'], "eid": tx['event_id'], "status": tx['status'], "tid": tx['ticket_id']})
        conn.commit()
    print("✅ Seeded Transactions")

    # 4. Seed Tickets
    engine = get_engine("ticket_db", 5435)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id VARCHAR PRIMARY KEY, user_id VARCHAR NOT NULL, event_id VARCHAR NOT NULL,
                transaction_id VARCHAR UNIQUE NOT NULL, status VARCHAR NOT NULL,
                issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checked_in_at TIMESTAMP WITH TIME ZONE
            );
        """))
        conn.execute(text("DELETE FROM tickets"))
        for tk in data['tickets']:
            checked_in = None
            if tk['status'] == 'used':
                checked_in = datetime.now(timezone.utc) - timedelta(hours=1)
            
            conn.execute(text("""
                INSERT INTO tickets (ticket_id, user_id, event_id, transaction_id, status, issued_at, checked_in_at)
                VALUES (:id, :uid, :eid, :tid, :status, NOW(), :cia)
            """), {"id": tk['id'], "uid": tk['user_id'], "eid": tk['event_id'], "tid": tk['transaction_id'], 
                   "status": tk['status'], "cia": checked_in})
        conn.commit()
    print("✅ Seeded Tickets")

if __name__ == "__main__":
    seed_all()
    print("\n🚀 Mock data is prepared!")
