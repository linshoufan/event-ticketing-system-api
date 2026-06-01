"""
涵蓋：
- 報名 confirmed
- 重複報名擋下
- 容量滿時自動進 waitlist
- 取消 confirmed → 自動補位
- 取消 waitlist
- update guest_count
- no-show punishment
- 福委會不能報名（FORBIDDEN_ROLE）
- locked 帳號不能報名
- cancellation deadline 過後不能取消
"""
import sys
import os
sys.path.insert(0, '.')

os.environ['TRANSACTION_DB_USER'] = 'txuser'
os.environ['TRANSACTION_DB_PASSWORD'] = 'txpass'
os.environ['TRANSACTION_DB_HOST'] = 'localhost'
os.environ['TRANSACTION_DB_PORT'] = '5432'
os.environ['TRANSACTION_DB_NAME'] = 'transaction_db'

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.core.database import SessionLocal
from app.core.dependencies import CurrentUser
from app.core.external import (
    EVENT_STATUS_REGISTERING,
    EventInfo,
    RegistrationProfile,
)
from app.models.transaction import Transaction
from app.services import transaction_service, no_show_service

now = datetime.now(timezone.utc)
USER_IDS = [f"user_{i:03d}" for i in range(5, 11)]

def make_profile(user_id, role="employee", locked=False, diet="non-veg", driving=False, username=None):
    return RegistrationProfile(
        user_id=user_id, role=role,
        registration_status="locked" if locked else "active",
        unlock_at=(now + timedelta(days=30)) if locked else None,
        autofill_diet_type=diet, autofill_self_driving=driving,
        preferences=[],
        username=username,
    )

def make_event(event_id, ticket_limit=None, cancellation_deadline=None,
               guest_allowed=False, registration_open=True):
    return EventInfo(
        event_id=event_id, name=f"Event {event_id}",
        status=EVENT_STATUS_REGISTERING,
        is_draft=False, guest_allowed=guest_allowed,
        ticket_limit=ticket_limit, remaining_tickets=0,
        cancellation_deadline=cancellation_deadline,
        registration_start=now - timedelta(days=1) if registration_open else now + timedelta(days=1),
        registration_end=now + timedelta(days=7),
        event_start_time=now + timedelta(days=10),
        event_end_time=now + timedelta(days=10, hours=4),
    )

def make_clients(profiles=None, events=None):
    """構造 mock clients。"""
    profiles = profiles or {}
    events = events or {}

    acc = MagicMock()
    acc.get_registration_profile.side_effect = lambda uid: profiles[uid]
    acc.punish_user.side_effect = lambda uid: {"userId": uid, "registrationStatus": "locked"}

    evt = MagicMock()
    evt.get_event.side_effect = lambda eid: events[eid]

    tkt = MagicMock()
    ticket_counter = [0]
    def issue(**kwargs):
        ticket_counter[0] += 1
        return f"ticket-{ticket_counter[0]}"
    tkt.issue_ticket.side_effect = issue
    tkt.void_ticket = MagicMock()
    tkt.list_unused_tickets = MagicMock(return_value=[])
    return acc, evt, tkt

def reset_db():
    db = SessionLocal()
    db.query(Transaction).delete()
    db.commit()
    db.close()

# TEST 1: Confirmed registration with autofill
def test_confirmed_registration():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006", diet="veg", driving=True)},
        events={"event_005": make_event("event_005", ticket_limit=2, guest_allowed=True)},
    )
    tx = transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=None,  # 不給 → 預設 0
        request_diet_type=None,    # 不給 → 走 autofill
        request_self_driving=None, # 不給 → 走 autofill
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    assert tx.status == "confirmed"
    assert tx.diet_type == "veg"           # autofill
    assert tx.self_driving is True          # autofill
    assert tx.guest_count == 0
    assert tx.ticket_id == "ticket-1"       # 已配發
    tkt.issue_ticket.assert_called_once()
    db.close()
    print("[PASS] test_confirmed_registration")


# TEST 2: Duplicate registration blocked
def test_duplicate_blocked():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006")},
        events={"event_005": make_event("event_005", ticket_limit=5)},
    )
    transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=None, request_diet_type=None, request_self_driving=None,
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    try:
        transaction_service.create_registration(
            user_id="user_006", event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        assert False, "should have raised"
    except Exception as exc:
        assert "ALREADY_REGISTERED" in str(exc.detail)
    db.close()
    print("[PASS] test_duplicate_blocked")

# TEST 3: Auto waitlist when full
def test_auto_waitlist():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={user_id: make_profile(user_id) for user_id in USER_IDS[:4]},
        events={"event_005": make_event("event_005", ticket_limit=2)},
    )
    statuses = []
    for i in range(4):
        tx = transaction_service.create_registration(
            user_id=USER_IDS[i], event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        statuses.append((tx.status, tx.waitlist_number, tx.ticket_id))
    assert statuses[0] == ("confirmed", None, "ticket-1")
    assert statuses[1] == ("confirmed", None, "ticket-2")
    assert statuses[2] == ("waitlist", 1, None)
    assert statuses[3] == ("waitlist", 2, None)
    db.close()
    print("[PASS] test_auto_waitlist")

# TEST 4: Cancel confirmed triggers waitlist promotion
def test_cancel_promotes_waitlist():
    reset_db()
    db = SessionLocal()
    deadline = now + timedelta(days=5)
    acc, evt, tkt = make_clients(
        profiles={user_id: make_profile(user_id) for user_id in USER_IDS[:3]},
        events={"event_005": make_event("event_005", ticket_limit=2, cancellation_deadline=deadline)},
    )
    txs = []
    for i in range(3):
        tx = transaction_service.create_registration(
            user_id=USER_IDS[i], event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        txs.append(tx)
    # user_005 confirmed, user_006 confirmed, user_007 waitlist#1
    assert txs[2].status == "waitlist"

    # user_005 cancels → user_007 should be promoted
    cancelled, promoted = transaction_service.cancel_registration(
        transaction_id=txs[0].transaction_id,
        current_user=CurrentUser(user_id="user_005", role="employee"),
        db=db, event_client=evt, ticket_client=tkt,
    )
    assert cancelled.status == "cancelled"
    assert cancelled.ticket_id is None  # 清掉了
    assert promoted is not None
    assert promoted.user_id == "user_007"
    assert promoted.status == "confirmed"
    assert promoted.waitlist_number is None
    assert promoted.ticket_id == "ticket-3"  # 新發

    tkt.void_ticket.assert_called_once_with("ticket-1")  # 舊的被作廢
    db.close()
    print("[PASS] test_cancel_promotes_waitlist")

# TEST 5: Cancel waitlist does NOT promote anyone
def test_cancel_waitlist():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={user_id: make_profile(user_id) for user_id in USER_IDS[:3]},
        events={"event_005": make_event("event_005", ticket_limit=1, cancellation_deadline=now+timedelta(days=5))},
    )
    txs = []
    for i in range(3):
        tx = transaction_service.create_registration(
            user_id=USER_IDS[i], event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        txs.append(tx)
    # user_005 confirmed, user_006 waitlist#1, user_007 waitlist#2
    # user_006 cancels (waitlist) → 沒人被升
    cancelled, promoted = transaction_service.cancel_registration(
        transaction_id=txs[1].transaction_id,
        current_user=CurrentUser(user_id="user_006", role="employee"),
        db=db, event_client=evt, ticket_client=tkt,
    )
    assert cancelled.status == "cancelled"
    assert promoted is None
    db.close()
    print("[PASS] test_cancel_waitlist")

# TEST 6: Cancellation deadline = None means NOT cancellable
def test_no_cancellation_deadline_blocks_cancel():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006")},
        events={"event_005": make_event("event_005", ticket_limit=5, cancellation_deadline=None)},
    )
    tx = transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=None, request_diet_type=None, request_self_driving=None,
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    try:
        transaction_service.cancel_registration(
            transaction_id=tx.transaction_id,
            current_user=CurrentUser(user_id="user_006", role="employee"),
            db=db, event_client=evt, ticket_client=tkt,
        )
        assert False, "should have raised"
    except Exception as exc:
        assert "NOT_CANCELLABLE" in str(exc.detail)
    db.close()
    print("[PASS] test_no_cancellation_deadline_blocks_cancel")

# TEST 7: Cancellation deadline passed
def test_cancellation_deadline_passed():
    reset_db()
    db = SessionLocal()
    past = now - timedelta(days=1)
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006")},
        events={"event_005": make_event("event_005", ticket_limit=5, cancellation_deadline=past)},
    )
    tx = transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=None, request_diet_type=None, request_self_driving=None,
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    try:
        transaction_service.cancel_registration(
            transaction_id=tx.transaction_id,
            current_user=CurrentUser(user_id="user_006", role="employee"),
            db=db, event_client=evt, ticket_client=tkt,
        )
        assert False
    except Exception as exc:
        assert "PAST_CANCELLATION_DEADLINE" in str(exc.detail)
    db.close()
    print("[PASS] test_cancellation_deadline_passed")

# TEST 8: welfare_member can't register
def test_welfare_member_blocked():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006", role="welfare_member")},
        events={"event_005": make_event("event_005", ticket_limit=5)},
    )
    try:
        transaction_service.create_registration(
            user_id="user_006", event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        assert False
    except Exception as exc:
        assert "FORBIDDEN_ROLE" in str(exc.detail)
    db.close()
    print("[PASS] test_welfare_member_blocked")

# TEST 9: Locked user blocked
def test_locked_user_blocked():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006", locked=True)},
        events={"event_005": make_event("event_005", ticket_limit=5)},
    )
    try:
        transaction_service.create_registration(
            user_id="user_006", event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        assert False
    except Exception as exc:
        assert "ACCOUNT_LOCKED" in str(exc.detail)
    db.close()
    print("[PASS] test_locked_user_blocked")

# TEST 10: Guest count rejected when guest not allowed
def test_guest_blocked():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006")},
        events={"event_005": make_event("event_005", ticket_limit=5, guest_allowed=False)},
    )
    tx = transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=2, request_diet_type=None, request_self_driving=None,
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    assert tx.status == "confirmed"
    assert tx.guest_count == 0
    db.close()
    print("[PASS] test_guest_blocked")

# TEST 11: Update guest_count
def test_update_registration():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={"user_006": make_profile("user_006")},
        events={"event_005": make_event("event_005", ticket_limit=None, guest_allowed=True)},
    )
    tx = transaction_service.create_registration(
        user_id="user_006", event_id="event_005",
        request_guest_count=0, request_diet_type=None, request_self_driving=None,
        db=db, account_client=acc, event_client=evt, ticket_client=tkt,
    )
    updated = transaction_service.update_registration(
        transaction_id=tx.transaction_id,
        current_user=CurrentUser(user_id="user_006", role="employee"),
        guest_count=3, diet_type="veg", self_driving=None,
        db=db, event_client=evt,
    )
    assert updated.guest_count == 3
    assert updated.diet_type == "veg"
    db.close()
    print("[PASS] test_update_registration")

# TEST 12: No-show punishment
def test_no_show_punishment():
    reset_db()
    db = SessionLocal()
    acc, evt, tkt = make_clients(
        profiles={user_id: make_profile(user_id) for user_id in USER_IDS[:3]},
        events={"event_005": make_event("event_005", ticket_limit=5)},
    )
    txs = []
    for i in range(3):
        tx = transaction_service.create_registration(
            user_id=USER_IDS[i], event_id="event_005",
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=db, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        txs.append(tx)
    # 假設 ticket-1 與 ticket-3 沒 check-in（user_005, user_007 爽約）
    tkt.list_unused_tickets.return_value = [txs[0].ticket_id, txs[2].ticket_id]

    result = no_show_service.punish_no_shows_for_event(
        event_id="event_005", db=db, ticket_client=tkt, account_client=acc,
    )
    assert sorted(result.punished_user_ids) == ["user_005", "user_007"]
    assert len(result.errors) == 0
    db.close()
    print("[PASS] test_no_show_punishment")
