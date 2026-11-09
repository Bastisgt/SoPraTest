import csv
import hashlib

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.conftest import DATASET_DIR

with (DATASET_DIR / "testcases.csv").open(encoding="utf-8", newline="") as _f:
    SEED_COUNT = sum(1 for _ in csv.DictReader(_f))

VIDEO = b"\x00\x00\x00\x18ftypmp42fake-video-bytes"


def upload(client: TestClient, filename: str = "clip.mp4", content: bytes = VIDEO, **form):
    data = {"name": "Uploaded clip", "expected_result": "NOK", "error_type": "flicker", "reference_id": "REF-001"}
    data.update(form)
    return client.post("/api/testcases", data=data, files={"file": (filename, content, "video/mp4")})


# --- read -------------------------------------------------------------------

def test_health(client: TestClient):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_seed_dataset_is_imported(client: TestClient):
    items = client.get("/api/testcases").json()
    assert len(items) == SEED_COUNT

    by_id = {tc["id"]: tc for tc in items}
    assert by_id["REF-001"]["kind"] == "reference"
    tc = by_id["TC-010"]
    assert tc["expected_result"] == "NOK"
    assert tc["error_type"] == "popup_delay"
    assert tc["category"] == "timing"
    assert tc["reference_id"] == "REF-001"
    assert tc["source"] == "seed"
    assert tc["manipulation"] == {"params": {"popupDelay": 500}}
    assert tc["video_url"] == "/api/testcases/TC-010/video"


def test_seed_is_idempotent(settings: Settings):
    for _ in range(2):
        with TestClient(create_app(settings)) as c:
            assert len(c.get("/api/testcases").json()) == SEED_COUNT


def test_filters(client: TestClient):
    refs = client.get("/api/testcases", params={"kind": "reference"}).json()
    assert [r["id"] for r in refs] == ["REF-001"]
    ok = client.get("/api/testcases", params={"expected_result": "OK", "kind": "testcase"}).json()
    assert all(tc["expected_result"] == "OK" for tc in ok) and ok


def test_get_unknown_returns_404(client: TestClient):
    assert client.get("/api/testcases/NOPE").status_code == 404


def test_video_is_served(client: TestClient):
    res = client.get("/api/testcases/REF-001/video")
    assert res.status_code == 200
    assert res.headers["content-type"] == "video/mp4"
    assert hashlib.sha256(res.content).hexdigest() == client.get("/api/testcases/REF-001").json()["sha256"]


def test_error_types(client: TestClient):
    types = {t["id"]: t["category"] for t in client.get("/api/error-types").json()}
    assert types["popup_delay"] == "timing"
    assert types["flicker"] == "display"


# --- upload (DS-07) ---------------------------------------------------------

def test_upload_testcase(client: TestClient):
    res = upload(client, id="MY-01", is_edge_case="true")
    assert res.status_code == 201, res.text
    tc = res.json()
    assert tc["id"] == "MY-01"
    assert tc["source"] == "upload"
    assert tc["category"] == "display"
    assert tc["is_edge_case"] is True
    assert tc["sha256"] == hashlib.sha256(VIDEO).hexdigest()
    assert client.get(tc["video_url"]).content == VIDEO
    assert len(client.get("/api/testcases").json()) == SEED_COUNT + 1


def test_upload_generates_id(client: TestClient):
    assert upload(client).json()["id"] == "UP-001"
    assert upload(client).json()["id"] == "UP-002"


def test_upload_reference(client: TestClient):
    res = upload(client, kind="reference", expected_result="OK", error_type="none", reference_id="")
    assert res.status_code == 201, res.text
    assert res.json()["reference_id"] is None


def test_upload_validation(client: TestClient):
    cases = [
        {"error_type": "none"},  # NOK without error type
        {"error_type": "does_not_exist"},
        {"reference_id": ""},  # test case without reference
        {"reference_id": "TC-010"},  # links to a test case, not a reference
        {"reference_id": "REF-999"},
        {"id": "../evil"},
        {"kind": "reference", "expected_result": "NOK"},
    ]
    for form in cases:
        assert upload(client, **form).status_code == 422, form
    assert upload(client, filename="notes.txt").status_code == 422


def test_upload_duplicate_id(client: TestClient):
    assert upload(client, id="TC-001").status_code == 409


def test_upload_too_large(client: TestClient, settings: Settings):
    res = upload(client, id="BIG", content=b"0" * (settings.max_upload_bytes + 1))
    assert res.status_code == 413
    assert not (settings.upload_dir / "BIG.mp4").exists()


# --- delete -----------------------------------------------------------------

def test_delete_upload(client: TestClient, settings: Settings):
    upload(client, id="DEL-1")
    assert client.delete("/api/testcases/DEL-1").status_code == 204
    assert client.get("/api/testcases/DEL-1").status_code == 404
    assert not (settings.upload_dir / "DEL-1.mp4").exists()


def test_seed_cannot_be_deleted(client: TestClient):
    assert client.delete("/api/testcases/TC-010").status_code == 403


def test_reference_in_use_cannot_be_deleted(client: TestClient):
    upload(client, id="REF-X", kind="reference", expected_result="OK", error_type="none", reference_id="")
    upload(client, id="TC-X", reference_id="REF-X")
    assert client.delete("/api/testcases/REF-X").status_code == 409
