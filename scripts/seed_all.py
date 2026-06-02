import yaml
import os
import argparse
import sys
from sqlalchemy import create_engine, text, inspect
from datetime import datetime, timezone, timedelta


def parse_datetime(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_engine(service, default_db_name, default_port):
    prefix = service.upper()
    user = os.getenv(f"{prefix}_DB_USER", "postgres")
    password = os.getenv(f"{prefix}_DB_PASSWORD", "postgres")
    host = os.getenv(f"{prefix}_DB_HOST", "localhost")
    port = os.getenv(f"{prefix}_DB_PORT", str(default_port))
    db_name = os.getenv(f"{prefix}_DB_NAME", default_db_name)
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(url)


def table_exists(engine, table_name):
    inspector = inspect(engine)
    try:
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def reset_tables(conn, *tables):
    table_list = ", ".join(tables)
    conn.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))


def preflight_schema(engines):
    required_tables = {
        "account": "users",
        "event": "events",
        "transaction": "transactions",
        "ticket": "tickets",
    }
    missing = [
        f"{service}.{table}"
        for service, table in required_tables.items()
        if not table_exists(engines[service], table)
    ]
    if missing:
        print("❌ Required tables are missing; seed aborted.")
        for item in missing:
            print(f"   - {item}")
        print("\nRun migrations first:")
        print("   cd backend/account && alembic upgrade head")
        print("   cd ../event && alembic upgrade head")
        print("   cd ../transaction && alembic upgrade head")
        print("   cd ../ticket && alembic upgrade head")
        return False
    return True


def seed_all(reset=False):
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(base_path, "scripts", "mock_data.yaml")
    
    if not os.path.exists(yaml_path):
        print(f"❌ Error: {yaml_path} not found.")
        return
        
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    engines = {
        "account": get_engine("account", "account_db", 5433),
        "event": get_engine("event", "event_db", 5432),
        "transaction": get_engine("transaction", "transaction_db", 5434),
        "ticket": get_engine("ticket", "ticket_db", 5435),
    }
    if not preflight_schema(engines):
        return False

    # 1. Seed Account Users
    engine = engines["account"]
    if table_exists(engine, "users"):
        with engine.connect() as conn:
            if reset:
                reset_tables(conn, "users")
            for u in data['users']:
                conn.execute(text("""
                    INSERT INTO users (user_id, username, email, role, registration_status, created_at, updated_at)
                    VALUES (:uid, :uid, :email, :role, 'active', NOW(), NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        email = EXCLUDED.email,
                        role = EXCLUDED.role,
                        updated_at = NOW()
                """), {"uid": u['user_id'], "email": u['email'], "role": u['role']})
            conn.commit()
        print(f"✅ Seeded Account Users")
    else:
        print("⚠️ Warning: 'users' table missing. Skipping Account Seed.")

    # 2. Seed Events
    engine = engines["event"]
    if table_exists(engine, "events"):
        with engine.connect() as conn:
            if reset:
                reset_tables(conn, "events")
            for ev in data['events']:
                start = parse_datetime(ev.get("event_start_time")) or (datetime.now(timezone.utc) + timedelta(hours=ev.get('time_offset', 0)))
                end = parse_datetime(ev.get("event_end_time")) or (start + timedelta(hours=ev.get('duration', 2)))
                reg_start = parse_datetime(ev.get("registration_start")) or (start + timedelta(days=ev.get('registration_offset', -7)))
                reg_end = parse_datetime(ev.get("registration_end")) or (start + timedelta(days=-1))
                cancel = parse_datetime(ev.get("cancellation_deadline")) or (start - timedelta(hours=ev.get('cancellation_offset', 24)))
                
                conn.execute(text("""
                    INSERT INTO events (event_id, name, description, location, category, event_start_time, event_end_time,
                                       registration_start, registration_end, cancellation_deadline, status, is_draft,
                                       latitude, longitude, checkin_radius_meters, guest_allowed, ticket_limit, remaining_tickets)
                    VALUES (:id, :name, :description, :loc, :cat, :start, :end, :rs, :re, :cd, :status, :is_draft,
                            :lat, :lon, :radius, :guest_allowed, :ticket_limit, :remaining_tickets)
                    ON CONFLICT (event_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        location = EXCLUDED.location,
                        category = EXCLUDED.category,
                        event_start_time = EXCLUDED.event_start_time,
                        event_end_time = EXCLUDED.event_end_time,
                        registration_start = EXCLUDED.registration_start,
                        registration_end = EXCLUDED.registration_end,
                        cancellation_deadline = EXCLUDED.cancellation_deadline,
                        status = EXCLUDED.status,
                        is_draft = EXCLUDED.is_draft,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        checkin_radius_meters = EXCLUDED.checkin_radius_meters,
                        guest_allowed = EXCLUDED.guest_allowed,
                        ticket_limit = EXCLUDED.ticket_limit,
                        remaining_tickets = EXCLUDED.remaining_tickets,
                        updated_at = NOW()
                """), {
                    "id": ev['id'], "name": ev['name'], "loc": ev['location'], "cat": ev['category'], 
                    "start": start, "end": end, "rs": reg_start, "re": reg_end, "cd": cancel, "status": ev['status'],
                    "description": ev.get("description", "Mock Description"),
                    "is_draft": ev.get("is_draft", False),
                    "lat": ev.get('lat', 25.0339), "lon": ev.get('lon', 121.5644), "radius": ev.get('radius', 500),
                    "guest_allowed": ev.get("guest_allowed", False),
                    "ticket_limit": ev.get("ticket_limit"),
                    "remaining_tickets": ev.get("remaining_tickets", 0),
                })
            conn.commit()
        print("✅ Seeded Events")
    else:
        print("⚠️ Warning: 'events' table missing. Skipping Event Seed.")

    # 3. Seed Transactions
    engine = engines["transaction"]
    if table_exists(engine, "transactions"):
        with engine.connect() as conn:
            if reset:
                reset_tables(conn, "transactions")
            for tx in data['transactions']:
                conn.execute(text("""
                    INSERT INTO transactions (transaction_id, user_id, event_id, status, ticket_id, guest_count, diet_type, self_driving, registered_at, updated_at)
                    VALUES (:id, :uid, :eid, :status, :tid, 0, 'non-veg', TRUE, NOW(), NOW())
                    ON CONFLICT (transaction_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        ticket_id = EXCLUDED.ticket_id,
                        updated_at = NOW()
                """), {"id": tx['id'], "uid": tx['user_id'], "eid": tx['event_id'], "status": tx['status'], "tid": tx['ticket_id']})
            conn.commit()
        print("✅ Seeded Transactions")

    # 4. Seed Tickets
    engine = engines["ticket"]
    if table_exists(engine, "tickets"):
        with engine.connect() as conn:
            if reset:
                reset_tables(conn, "tickets")
            for tk in data['tickets']:
                checked_in = datetime.now(timezone.utc) - timedelta(hours=1) if tk['status'] == 'used' else None
                conn.execute(text("""
                    INSERT INTO tickets (ticket_id, user_id, event_id, transaction_id, status, issued_at, checked_in_at)
                    VALUES (:id, :uid, :eid, :tid, :status, NOW(), :cia)
                    ON CONFLICT (ticket_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        checked_in_at = EXCLUDED.checked_in_at
                """), {"id": tk['id'], "uid": tk['user_id'], "eid": tk['event_id'], "tid": tk['transaction_id'], 
                       "status": tk['status'], "cia": checked_in})
            conn.commit()
        print("✅ Seeded Tickets")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed shared mock data.")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if not seed_all(reset=args.reset):
        sys.exit(1)
    print("\n🚀 Mock data is synchronized!")
