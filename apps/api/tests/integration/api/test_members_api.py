"""Phase 9 Integration Tests: Collaboration / Event Members API"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, RoleType
from app.models.event import Event
from app.models.user import User


def _setup_members_env(db: Session):
    organizer = User(name="Sarah Owner", email="sarah.o@eventra.test")
    collab = User(name="Carl Collab", email="carl.c@eventra.test")
    viewer = User(name="Val Viewer", email="val.v@eventra.test")
    db.add_all([organizer, collab, viewer])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Community Summit",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        state=EventState.NORMAL.value,
    )
    db.add(event)
    db.commit()

    return organizer, collab, viewer, event


def test_member_lifecycle_and_role_management(test_client: TestClient, db_session: Session):
    organizer, collab, viewer, event = _setup_members_env(db_session)

    # 1. Organizer adds collab
    add_resp = test_client.post(
        f"/api/events/{event.id}/members",
        json={"user_id": collab.id, "role": RoleType.COLLABORATOR.value},
        headers={"x-user-id": organizer.id},
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["role"] == RoleType.COLLABORATOR.value

    # 2. Organizer updates collab role to VIEWER
    patch_resp = test_client.patch(
        f"/api/events/{event.id}/members/{collab.id}",
        json={"role": RoleType.VIEWER.value},
        headers={"x-user-id": organizer.id},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["role"] == RoleType.VIEWER.value

    # 3. Collab attempts to update roles (Forbidden)
    collab_patch_resp = test_client.patch(
        f"/api/events/{event.id}/members/{collab.id}",
        json={"role": RoleType.MAIN_ORGANIZER.value},
        headers={"x-user-id": collab.id},
    )
    assert collab_patch_resp.status_code == 403

    # 4. Collab attempts to delete organizer (Forbidden)
    del_forbidden_resp = test_client.delete(
        f"/api/events/{event.id}/members/{organizer.id}",
        headers={"x-user-id": collab.id},
    )
    assert del_forbidden_resp.status_code == 403

    # 5. Organizer attempts to remove themselves (MAIN_ORGANIZER) -> Bad Request
    del_owner_resp = test_client.delete(
        f"/api/events/{event.id}/members/{organizer.id}",
        headers={"x-user-id": organizer.id},
    )
    assert del_owner_resp.status_code == 400
    assert "Cannot remove the MAIN_ORGANIZER" in del_owner_resp.json()["detail"]

    # 6. Organizer removes collaborator -> 204 No Content
    del_resp = test_client.delete(
        f"/api/events/{event.id}/members/{collab.id}",
        headers={"x-user-id": organizer.id},
    )
    assert del_resp.status_code == 204

    # 7. List members confirms only organizer remains
    list_resp = test_client.get(
        f"/api/events/{event.id}/members",
        headers={"x-user-id": organizer.id},
    )
    assert list_resp.status_code == 200
    members = list_resp.json()
    assert len(members) == 1
    assert members[0]["user_id"] == organizer.id
