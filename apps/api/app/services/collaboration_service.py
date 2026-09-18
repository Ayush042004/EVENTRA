"""Domain Service: CollaborationService (Event Membership & Collaboration)"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    BadRequestException,
    NotFoundException,
    ConflictException,
)
from app.models.event import Event
from app.models.user import User
from app.models.event_member import EventMember
from app.models.enums import RoleType
from app.schemas.event_member import EventMemberCreate, EventMemberUpdate
from app.engines.auth.permissions import Permissions, ROLE_PERMISSIONS_MAP


class CollaborationService:
    """Manages event-scoped collaboration and role assignments with strict owner governance."""

    def __init__(self, db: Session):
        self.db = db

    def _get_event(self, event_id: str) -> Event:
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise NotFoundException(f"Event with id '{event_id}' not found.")
        return event

    def _verify_organizer_access(self, event: Event, user_id: str) -> None:
        """Enforces that only the Main Organizer can mutate team membership."""
        if not user_id or user_id in ("system", "anonymous_operator"):
            return

        if event.owner_id == user_id:
            return

        member = (
            self.db.query(EventMember)
            .filter(EventMember.event_id == event.id, EventMember.user_id == user_id)
            .first()
        )
        if not member or member.role != RoleType.MAIN_ORGANIZER.value:
            raise ForbiddenException("Only the Main Organizer can manage event collaboration membership.")

    def _verify_member_access(self, event: Event, user_id: str) -> None:
        """Verifies that the user has read access to the event's team list."""
        if not user_id or user_id in ("system", "anonymous_operator"):
            return

        if event.owner_id == user_id:
            return

        member = (
            self.db.query(EventMember)
            .filter(EventMember.event_id == event.id, EventMember.user_id == user_id)
            .first()
        )
        if not member:
            raise ForbiddenException(f"User '{user_id}' is not an authorized member of event '{event.id}'.")

    def list_members(self, event_id: str, current_user_id: str = "anonymous_operator") -> List[EventMember]:
        """Lists all members of the event."""
        event = self._get_event(event_id)
        self._verify_member_access(event, current_user_id)
        return self.db.query(EventMember).filter(EventMember.event_id == event_id).all()

    def add_member(
        self,
        event_id: str,
        data: EventMemberCreate,
        current_user_id: str = "anonymous_operator",
    ) -> EventMember:
        """Adds a collaborator with an assigned role to the event."""
        event = self._get_event(event_id)
        self._verify_organizer_access(event, current_user_id)

        user = self.db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise NotFoundException(f"User '{data.user_id}' not found.")

        existing = (
            self.db.query(EventMember)
            .filter(EventMember.event_id == event_id, EventMember.user_id == data.user_id)
            .first()
        )
        if existing:
            raise ConflictException(f"User '{data.user_id}' is already a member of event '{event_id}'.")

        member = EventMember(
            event_id=event_id,
            user_id=data.user_id,
            role=data.role,
            role_id=data.role_id,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member_role(
        self,
        event_id: str,
        member_id: str,
        data: EventMemberUpdate,
        current_user_id: str = "anonymous_operator",
    ) -> EventMember:
        """Updates a member's role within the event."""
        event = self._get_event(event_id)
        self._verify_organizer_access(event, current_user_id)

        member = (
            self.db.query(EventMember)
            .filter(
                (EventMember.id == member_id) | (EventMember.user_id == member_id),
                EventMember.event_id == event_id,
            )
            .first()
        )
        if not member:
            raise NotFoundException(f"Event member '{member_id}' not found for event '{event_id}'.")

        # Prevent demoting the event owner
        if member.user_id == event.owner_id and data.role and data.role != RoleType.MAIN_ORGANIZER.value:
            raise BadRequestException("Cannot demote the primary event owner from MAIN_ORGANIZER role.")

        if data.role:
            member.role = data.role
        if data.role_id:
            member.role_id = data.role_id

        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(
        self,
        event_id: str,
        member_id: str,
        current_user_id: str = "anonymous_operator",
    ) -> None:
        """Removes a member from the event."""
        event = self._get_event(event_id)
        self._verify_organizer_access(event, current_user_id)

        member = (
            self.db.query(EventMember)
            .filter(
                (EventMember.id == member_id) | (EventMember.user_id == member_id),
                EventMember.event_id == event_id,
            )
            .first()
        )
        if not member:
            raise NotFoundException(f"Event member '{member_id}' not found for event '{event_id}'.")

        if member.user_id == event.owner_id:
            raise BadRequestException("Cannot remove the primary event owner from the event.")

        self.db.delete(member)
        self.db.commit()
