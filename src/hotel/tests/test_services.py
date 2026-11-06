import datetime as dt

from django.test import TestCase

from hotel.models import Booking, Room
from hotel.services import BookingConflictError, booking_create


class BookingCreateServiceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(description="Test room", price="1000.00")
        Booking.objects.create(
            room=cls.room, date_start=dt.date(2026, 6, 20), date_end=dt.date(2026, 6, 25)
        )

    def test_overlapping_dates_rejected(self):
        cases = [
            (dt.date(2026, 6, 23), dt.date(2026, 6, 27)),  # заходит справа
            (dt.date(2026, 6, 18), dt.date(2026, 6, 22)),  # заходит слева
            (dt.date(2026, 6, 21), dt.date(2026, 6, 22)),  # целиком внутри
            (dt.date(2026, 6, 18), dt.date(2026, 6, 30)),  # целиком накрывает
            (dt.date(2026, 6, 20), dt.date(2026, 6, 25)),  # точно совпадает
        ]
        for date_start, date_end in cases:
            with (
                self.subTest(date_start=date_start, date_end=date_end),
                self.assertRaises(BookingConflictError),
            ):
                booking_create(room=self.room, date_start=date_start, date_end=date_end)

        self.assertEqual(Booking.objects.count(), 1)

    def test_adjacent_dates_allowed(self):
        booking_create(
            room=self.room, date_start=dt.date(2026, 6, 25), date_end=dt.date(2026, 6, 27)
        )
        booking_create(
            room=self.room, date_start=dt.date(2026, 6, 15), date_end=dt.date(2026, 6, 20)
        )

        self.assertEqual(Booking.objects.count(), 3)

    def test_other_room_not_affected(self):
        other_room = Room.objects.create(description="Other room", price="2000.00")

        booking = booking_create(
            room=other_room, date_start=dt.date(2026, 6, 20), date_end=dt.date(2026, 6, 25)
        )

        self.assertEqual(booking.room, other_room)
