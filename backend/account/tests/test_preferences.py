from app.core.config import settings
from app.models.user import UserPreference
from app.services import user_service

VALID_KEY = settings.internal_api_key
HEADER = "X-Internal-Key"


def test_resolve_autofill_uses_category_then_falls_back(make_user, db_session):
    """有該 category 設定 → 用它；該欄位是 None 或沒這個 category → fallback 全域。"""
    user = make_user(role="employee") 
    db_session.add(UserPreference(
        user_id=user.user_id, category="family",
        diet_type="veg", self_driving=True, guest_count=2,
    ))
    db_session.commit()

    # 命中 family → 回該類別的值
    hit = user_service.resolve_autofill(user=user, category="family", db=db_session)
    assert hit == {"dietType": "veg", "selfDriving": True, "guestCount": 2}

    # 沒有 sport 這個類別 → guestCount 為 None，diet/driving fallback 全域
    miss = user_service.resolve_autofill(user=user, category="sport", db=db_session)
    assert miss["guestCount"] is None


def test_registration_profile_with_category(client, make_user, db_session):
    user = make_user(role="employee")
    db_session.add(UserPreference(
        user_id=user.user_id, category="family",
        diet_type="veg", self_driving=True, guest_count=3,
    ))
    db_session.commit()

    resp = client.get(
        f"/v1/internal/users/{user.user_id}/registration-profile?category=family",
        headers={HEADER: VALID_KEY},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["autofill"] == {
        "dietType": "veg", "selfDriving": True, "guestCount": 3,
    }


def test_patch_autofill_upserts_category(client, make_user, db_session):
    user = make_user(role="employee")
    resp = client.patch(
        f"/v1/internal/users/{user.user_id}/autofill",
        headers={HEADER: VALID_KEY},
        json={"category": "family", "dietType": "veg", "selfDriving": True, "guestCount": 4},
    )
    assert resp.status_code == 200
    pref = (
        db_session.query(UserPreference)
        .filter_by(user_id=user.user_id, category="family")
        .first()
    )
    assert pref is not None
    assert (pref.diet_type, pref.self_driving, pref.guest_count) == ("veg", True, 4)