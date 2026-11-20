"""Medical records (Dashboard spec §14, SECURITY.md §8, §25 test 1 for these routes). A fake
Storage stands in for the private bucket, so no test reaches a real Supabase project.
Runs against alovia-test."""

import re
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.core.errors import AppError
from tests.helpers import add_doctor, add_linked_patient, assign, bearer, make_app

API = "/api/v1/doctor"
PDF = b"%PDF-1.7\n test file"
PNG = b"\x89PNG\r\n\x1a\n test image"
JPG = b"\xff\xd8\xff\xe0 test image"


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, tuple[bytes, str]] = {}
        self.down = False

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        if self.down:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is not available.", status=503)
        assert path not in self.files  # never replaced
        self.files[path] = (data, content_type)

    def signed_url(self, path: str, seconds: int) -> str:
        assert path in self.files
        return f"https://storage.example.test/signed/{path}?ttl={seconds}"


@pytest.fixture(scope="module")
def app(test_db_url: str, engine: Engine) -> Iterator[FastAPI]:
    application: FastAPI = make_app(database_url=test_db_url)
    application.state.storage = FakeStorage()
    yield application
    application.state.engine.dispose()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def storage(app: FastAPI) -> FakeStorage:
    fake: FakeStorage = app.state.storage
    fake.down = False
    return fake


def setup(engine: Engine) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    user, doctor_id = add_doctor(engine)
    _, patient_id = add_linked_patient(engine)
    assign(engine, doctor_id, patient_id, primary=True)
    return bearer(sub=str(user)), patient_id, doctor_id


def upload(
    client: TestClient,
    h: dict[str, str],
    pid: uuid.UUID,
    name: str = "scan.pdf",
    data: bytes = PDF,
    file_type: str = "ultrasound",
    **form: str,
) -> Any:
    return client.post(
        f"{API}/patients/{pid}/records",
        files={"file": (name, data, "application/octet-stream")},
        data={"file_type": file_type, **form},
        headers=h,
    )


def rows(engine: Engine, pid: uuid.UUID) -> int:
    with engine.connect() as conn:
        n: int = conn.execute(
            text("SELECT count(*) FROM medical_records WHERE patient_id = :p"), {"p": pid}
        ).scalar_one()
    return n


def test_upload_list_and_download(client: TestClient, engine: Engine, storage: FakeStorage) -> None:
    h, pid, _ = setup(engine)
    res = upload(client, h, pid, name="C:\\fake\\my scan.pdf", note=" Test note ")
    assert res.status_code == 201
    out = res.json()["data"]
    assert out["original_filename"] == "my scan.pdf" and out["note"] == "Test note"
    assert out["uploaded_by_name"] == "Test Doctor" and out["file_type"] == "ultrasound"
    with engine.connect() as conn:
        path = conn.execute(
            text("SELECT storage_path FROM medical_records WHERE id = :i"), {"i": out["id"]}
        ).scalar_one()
    assert re.fullmatch(rf"patients/{pid}/[0-9a-f-]{{36}}\.pdf", path)
    assert storage.files[path] == (PDF, "application/pdf")

    assert upload(client, h, pid, name="photo.JPEG", data=JPG, file_type="other").status_code == 201
    assert (
        upload(client, h, pid, name="lab.png", data=PNG, file_type="blood_report").status_code
        == 201
    )
    listed = client.get(f"{API}/patients/{pid}/records", headers=h).json()["data"]
    assert [r["original_filename"] for r in listed] == ["lab.png", "photo.JPEG", "my scan.pdf"]

    link = client.get(f"{API}/records/{out['id']}/download", headers=h).json()["data"]
    assert link == {"url": f"https://storage.example.test/signed/{path}?ttl=300", "expires_in": 300}
    with engine.connect() as conn:
        actions = list(
            conn.execute(
                text("SELECT action FROM audit_log WHERE patient_id = :p ORDER BY created_at"),
                {"p": pid},
            ).scalars()
        )
    assert actions.count("record uploaded") == 3 and actions.count("record downloaded") == 1


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("scan.pdf", PNG),  # extension and signature disagree
        ("scan.png", PDF),
        ("scan.gif", b"GIF89a"),
        ("scan", PDF),  # no extension
        ("scan.exe.pdf", b"MZ\x90\x00"),
    ],
)
def test_wrong_files_are_refused_with_415(
    client: TestClient, engine: Engine, storage: FakeStorage, name: str, data: bytes
) -> None:
    h, pid, _ = setup(engine)
    before = len(storage.files)
    res = upload(client, h, pid, name=name, data=data)
    assert res.status_code == 415 and res.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert len(storage.files) == before and rows(engine, pid) == 0


def test_too_large_and_bad_form_are_refused(
    client: TestClient, engine: Engine, storage: FakeStorage
) -> None:
    h, pid, _ = setup(engine)
    big = PDF + b"0" * (10 * 1024 * 1024)
    res = upload(client, h, pid, data=big)
    assert res.status_code == 413 and res.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert upload(client, h, pid, file_type="xray").status_code == 400
    assert upload(client, h, pid, note="x" * 501).status_code == 400
    assert rows(engine, pid) == 0


def test_storage_down_saves_nothing(
    client: TestClient, engine: Engine, storage: FakeStorage
) -> None:
    h, pid, _ = setup(engine)
    storage.down = True
    assert upload(client, h, pid).status_code == 503
    assert rows(engine, pid) == 0


def test_other_doctors_get_an_inbox_item(
    client: TestClient, engine: Engine, storage: FakeStorage
) -> None:
    h, pid, _ = setup(engine)
    upload(client, h, pid)  # only doctor: no item
    other_user, other_id = add_doctor(engine)
    assign(engine, other_id, pid)
    rid = upload(client, h, pid).json()["data"]["id"]
    with engine.connect() as conn:
        items = conn.execute(
            text("SELECT type, ref_table, ref_id FROM inbox_items WHERE patient_id = :p"),
            {"p": pid},
        ).all()
    assert [tuple(i) for i in items] == [("record_uploaded", "medical_records", uuid.UUID(rid))]


def test_other_doctors_patients_records_are_hidden(
    client: TestClient, engine: Engine, storage: FakeStorage
) -> None:
    h, pid, _ = setup(engine)
    rid = upload(client, h, pid).json()["data"]["id"]
    stranger = bearer(sub=str(add_doctor(engine)[0]))
    assert client.get(f"{API}/patients/{pid}/records", headers=stranger).status_code == 404
    assert upload(client, stranger, pid).status_code == 404
    assert client.get(f"{API}/records/{rid}/download", headers=stranger).status_code == 404
    assert client.get(f"{API}/records/{uuid.uuid4()}/download", headers=h).status_code == 404
