"""
Tests for Tamil Voice Assistant and Owner Voice Recording Input Engine.
Covers language identification, department classification, entity extraction,
intent analysis, live query responses, and action confirmation.
"""
import pytest
from app import create_app
from app.voice.intent_engine import (
    detect_language,
    identify_department,
    extract_numbers,
    analyze_voice_intent
)

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()


def test_language_detection():
    # Pure Tamil
    assert detect_language("முருக்கு பிரிவில் இன்றைக்கு மூன்று பேட்ச்கள் தயாரிக்க வேண்டும்.") == "TAMIL"
    # Pure English
    assert detect_language("Show today's total production details.") == "ENGLISH"
    # Mixed / Tanglish
    assert detect_language("Murukku section la 3 batches start pannunga") == "TAMIL_ENGLISH_MIXED"
    assert detect_language("இன்றைய production report கொடுங்க") == "TAMIL_ENGLISH_MIXED"


def test_department_detection():
    _, d1 = identify_department("முருக்கு பிரிவில் முதல் பேட்ச் தொடங்கவும்")
    assert d1 == "Murukku Production"

    _, d2 = identify_department("உருளைக்கிழங்கு சிப்ஸ் ஸ்லைஸ் மிஷின் பிரச்சனை")
    assert d2 == "Potato Chips Production"

    _, d3 = identify_department("வாழைக்காய் சிப்ஸ் பேக்கிங் செய்யுங்கள்")
    assert d3 == "Banana Chips Production"

    _, d4 = identify_department("மிக்சர் பிரிவில் கடலைப் பருப்பு குறைவாக உள்ளது")
    assert d4 == "Mixture Production"

    _, d5 = identify_department("மைசூர் பாக் பிரிவில் நெய் சேர்க்கும் வேலை")
    assert d5 == "Mysore Pak Production"

    _, d6 = identify_department("மூலப்பொருள் கிடங்கில் மாவு இருப்பு")
    assert d6 == "Raw Material Warehouse"


def test_number_and_quantity_extraction():
    # Tamil word numbers
    nums_1 = extract_numbers("முருக்கு பிரிவில் இன்றைக்கு மூன்று பேட்ச்கள் தயாரிக்க வேண்டும்.")
    assert 3 in nums_1

    # Digits and units
    nums_2 = extract_numbers("முதல் பேட்சில் 188 பாக்கெட்டுகள் தயாராகியுள்ளன, ஆறு பாக்கெட்டுகள் சேதமடைந்துவிட்டன.")
    assert 188 in nums_2
    assert 6 in nums_2

    # Weight in kg
    nums_3 = extract_numbers("இந்த பேட்சில் 150 கிலோ உருளைக்கிழங்கு பயன்படுத்தப்பட்டுள்ளது.")
    assert 150 in nums_3

    # Currency
    nums_4 = extract_numbers("விற்பனையாளரிடமிருந்து 4000 ரூபாய் வசூலிக்கப்பட்டுள்ளது.")
    assert 4000 in nums_4


def test_general_factory_status_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "நம்முடைய Smart Food Manufacturing Factory-யின் இன்றைய நிலவரத்தை சொல்லுங்கள்.",
            db=db
        )
        assert res["intent_category"] == "GENERAL_QUERY"
        assert res["action_type"] == "STATUS_REPORT"
        assert res["assistant_answer"] is not None
        assert "Smart Food Manufacturing Factory" in res["assistant_answer"]
        assert "உற்பத்தி" in res["assistant_answer"] or "பேட்ச்" in res["assistant_answer"]


def test_murukku_batch_output_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "இன்றைய முதல் பேட்சில் 188 பாக்கெட்டுகள் தயாராகியுள்ளன. ஆறு பாக்கெட்டுகள் சேதமடைந்துவிட்டன.",
            db=db
        )
        assert res["intent_category"] == "PRODUCTION"
        assert res["action_type"] == "BATCH_COMPLETE"
        assert res["entities"]["actual_quantity"] == 188
        assert res["entities"]["damaged_quantity"] == 6
        assert "188" in res["proposed_action"]


def test_machine_breakdown_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "முருக்கு பிழியும் இயந்திரத்தில் மோட்டார் சத்தம் அதிகமாக உள்ளது, உடனே பராமரிப்பு குழுவை அழையுங்கள்.",
            db=db
        )
        assert res["action_type"] in ["MACHINE_BREAKDOWN", "MACHINE_DOWNTIME", "MAINTENANCE_LOG", "EMERGENCY_ALERT"]
        assert "Murukku" in res["proposed_action"] or "Machinery" in res["proposed_action"]


def test_labour_overtime_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "குமரவேல் இன்று இரண்டு மணி நேரம் கூடுதல் வேலை செய்துள்ளார், அதை பதிவு செய்யுங்கள்.",
            db=db
        )
        assert res["action_type"] == "OVERTIME_LOG"
        assert res["entities"]["overtime_minutes"] == 120
        assert "குமரவேல்" in res["proposed_action"] or "Kumaravel" in res["proposed_action"]


def test_emergency_halt_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "அவசர நிலை! உடனடியாக அனைத்து இயந்திரங்களையும் நிறுத்துங்கள்!",
            db=db
        )
        assert res["intent_category"] == "EMERGENCY"
        assert res["action_type"] == "EMERGENCY_ALERT"
        assert res["is_high_risk"] is True
        assert "EMERGENCY" in res["proposed_action"]


def test_customer_payment_intent(app):
    with app.app_context():
        db = app.extensions["database"]
        res = analyze_voice_intent(
            "சில்லறை விற்பனையாளர் A-விடமிருந்து 4000 ரூபாய் வசூலிக்கப்பட்டுள்ளது.",
            db=db
        )
        assert res["action_type"] == "PAYMENT_RECEIPT"
        assert res["entities"]["payment_amount"] == 4000
        assert "4000" in res["proposed_action"] or "4,000" in res["proposed_action"]


def test_location_prefill_and_voice_routes(client):
    # Log in as Owner
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess.get("csrf_token", "")
    login_resp = client.post("/login", data={
        "identifier": "owner@smartfactory.com",
        "password": "Owner@123",
        "csrf_token": csrf
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    # Test voice record page with department and location prefill from 2D map
    rec_resp = client.get("/voice/record?department_id=1&location_id=1")
    assert rec_resp.status_code == 200
    assert b"Murukku Production" in rec_resp.data
    assert b"Start Recording" in rec_resp.data
    assert b"Tamil Speech-to-Text" in rec_resp.data

    # Test submitting a voice transcript
    with client.session_transaction() as sess:
        csrf = sess.get("csrf_token", "")
    post_resp = client.post("/voice/record", data={
        "title": "Murukku dough status",
        "language": "TAMIL",
        "module_name": "Murukku Production",
        "transcript": "முருக்கு பிரிவில் முதல் பேட்ச் மாவு தயாரிக்கும் வேலை முடிந்துவிட்டது.",
        "duration_seconds": "18",
        "csrf_token": csrf
    }, follow_redirects=True)
    assert post_resp.status_code == 200
    assert "முருக்கு பிரிவில்".encode("utf-8") in post_resp.data

    # Test voice library filter
    lib_resp = client.get("/voice/library?language=TAMIL")
    assert lib_resp.status_code == 200
    assert b"Central Voice Records Library" in lib_resp.data
