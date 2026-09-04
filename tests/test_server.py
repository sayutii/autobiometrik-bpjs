import pytest
from autobiometrik.config import Config
from autobiometrik.server import create_app


@pytest.fixture
def client():
    config = Config({
        "frista_username": "test_user",
        "frista_password": "test_pass",
        "finger_username": "finger_test",
        "finger_password": "finger_pass"
    })
    app = create_app(config)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "autobiometrik-bpjs"
    assert data["has_credentials"] is True
    assert data["has_finger_credentials"] is True
    assert data["scheme"] == "http"


def test_start_frista_success(client):
    response = client.get("/start_frista?no_peserta=0001234567890")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "running"
    assert data["target"] == "frista"
    assert data["no_peserta"] == "0001234567890"


def test_start_frista_missing_param(client):
    response = client.get("/start_frista")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "no_peserta" in data["message"]


def test_start_finger_success(client):
    response = client.get("/start_finger?no_peserta=0001234567890")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "running"
    assert data["target"] == "finger"
    assert data["no_peserta"] == "0001234567890"


def test_start_finger_missing_param(client):
    response = client.get("/start_finger")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "no_peserta" in data["message"]


def test_stop_frista(client):
    response = client.get("/stop_frista")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "FRISTA stopped" in data["message"]


def test_stop_finger(client):
    response = client.get("/stop_finger")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "sidik jari stopped" in data["message"]
