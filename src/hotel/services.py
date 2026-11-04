from .models import Booking


class BookingConflictError(Exception):
    pass


def booking_create(*, room, date_start, date_end):
    has_overlap = Booking.objects.filter(
        room=room,
        date_start__lt=date_end,
        date_end__gt=date_start,
    ).exists()

    if has_overlap:
        raise BookingConflictError("Room is already booked for these dates.")

    return Booking.objects.create(room=room, date_start=date_start, date_end=date_end)
