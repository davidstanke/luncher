import os
import json

from . import bookings

_APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_members_file() -> str:
    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        candidate = os.path.join(data_dir, "team_members.json")
        if os.path.exists(candidate):
            return candidate

    # repo root: app -> luncher_agent -> agents -> repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(_APP_DIR)))
    root_candidate = os.path.join(repo_root, "data", "team_members.json")
    if os.path.exists(root_candidate):
        return root_candidate

    local_candidate = os.path.join(_APP_DIR, "data", "team_members.json")
    return local_candidate


def get_team_members() -> list[dict]:
    """Loads and returns the team members' profiles and weekly availability schedules.

    This lists each member's timezone and weekly availability slots.
    """
    print("[Scheduling Subagent] Fetching team members profiles...")
    members_file = _resolve_members_file()
    try:
        if os.path.exists(members_file):
            with open(members_file, "r") as f:
                return json.load(f)
        print(f"[Scheduling Subagent] Warning: Members file not found at {members_file}")
        return []
    except Exception as e:
        print(f"[Scheduling Subagent] Error reading {members_file}: {e}")
        return []


async def book_meeting(time_slot: str, reason: str = "") -> str:
    """Records a confirmed meeting in the shared team bookings.

    Args:
        time_slot: The day and time range of the confirmed meeting, e.g., "Monday 10:00-11:00".
        reason: Optional brief reason/summary for selecting this choice.
    """
    print(f"[Scheduling Subagent] Finalizing booking: {time_slot}...")
    try:
        booking = await bookings.add_booking(time_slot, reason)
        return (
            f"Successfully booked! Meeting scheduled for {time_slot}. "
            f"Booking ID: {booking['booking_id']}."
        )
    except Exception as e:
        return f"Failed to book meeting: {str(e)}"


async def get_bookings() -> str:
    """Lists every meeting already booked by the team, oldest first.

    Bookings are shared across the whole team, so this returns the same list
    regardless of who asks. Use it to avoid double-booking a slot.
    """
    print("[Scheduling Subagent] Fetching existing team bookings...")
    try:
        existing = await bookings.list_bookings()
        if not existing:
            return "No meetings are currently booked."
        lines = [
            f"- {b['time_slot']}"
            + (f" ({b['reason']})" if b.get("reason") else "")
            + f" (booking {b['booking_id']})"
            for b in existing
        ]
        return "Existing team bookings:\n" + "\n".join(lines)
    except Exception as e:
        return f"Failed to read bookings: {str(e)}"


async def cancel_booking(booking_id: str) -> str:
    """Cancels a booked meeting, freeing its time slot for the whole team.

    Args:
        booking_id: Id of the booking to cancel, as shown by `get_bookings`,
            e.g. "bk_1786830033". Call `get_bookings` first if the user named a
            day rather than an id -- cancelling the wrong meeting is not undoable.
    """
    print(f"[Scheduling Subagent] Cancelling booking {booking_id}...")
    try:
        if await bookings.delete_booking(booking_id):
            return f"Successfully cancelled booking {booking_id}. The slot is free again."
        return f"Booking {booking_id} not found. Use 'get_bookings' to check existing IDs."
    except Exception as e:
        return f"Failed to cancel booking: {str(e)}"


async def cancel_all_bookings(expected_count: int) -> str:
    """Cancels every meeting booked by the team, but only if the count matches.

    Args:
        expected_count: Number of bookings currently on the calendar.
            Must match the count from `get_bookings` exactly.
    """
    print(f"[Scheduling Subagent] Cancelling all {expected_count} team bookings...")
    try:
        deleted = await bookings.delete_all_bookings(expected_count)
        if deleted < 0:
            return (
                "Calendar was modified since you checked it -- no bookings were "
                "cancelled. Call 'get_bookings' to see what changed and confirm again."
            )
        return f"Successfully cleared the team calendar ({deleted} bookings removed)."
    except Exception as e:
        return f"Failed to clear bookings: {str(e)}"
