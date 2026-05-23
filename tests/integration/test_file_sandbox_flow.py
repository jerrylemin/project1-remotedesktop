from __future__ import annotations


async def test_file_upload_dispatch_and_job(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    upload = await api_client.post("/api/files/upload", headers=headers, files={"file": ("demo.py", b"print('ok')", "text/x-python")})
    assert upload.status_code == 200
    artifact_id = upload.json()["artifact_id"]
    dispatch = await api_client.post(f"/api/files/{artifact_id}/dispatch", headers=headers, params={"machine_id": "m1"})
    assert dispatch.status_code == 200
    job = await api_client.post("/api/jobs", headers=headers, json={"machine_id": "m1", "command": "python demo.py", "timeout": 5})
    assert job.status_code == 200
    fetched = await api_client.get(f"/api/jobs/{job.json()['id']}", headers=headers)
    assert fetched.status_code == 200

