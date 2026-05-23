from __future__ import annotations


async def test_enroll_token_creates_machine(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    token_response = await api_client.post("/api/enroll-tokens", headers=headers)
    assert token_response.status_code == 200
    enroll_token = token_response.json()["enroll_token"]
    response = await api_client.post(
        "/api/agents/enroll",
        json={"enroll_token": enroll_token, "hostname": "lab-pc", "os": "Windows", "username": "student"},
    )
    assert response.status_code == 200
    assert response.json()["machine_secret"]

