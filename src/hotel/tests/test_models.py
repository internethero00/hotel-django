import datetime as dt

from django.db import IntegrityError, transaction
from django.test import TestCase

from hotel.models import Booking, Room


class RoomModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(description="Test room", price="1000.00")

    def test_str(self):
        self.assertEqual(str(self.room), f"Room #{self.room.id} ($1000.00)")

    def test_price_field_precision(self):
        field = Room._meta.get_field("price")
        self.assertEqual(field.max_digits, 10)
        self.assertEqual(field.decimal_places, 2)

    def test_created_at_set_automatically(self):
        self.assertIsNotNone(self.room.created_at)

    def test_zero_price_rejected_by_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Room.objects.create(description="Free room", price="0.00")


class BookingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(description="Test room", price="1000.00")

    def test_end_before_start_rejected_by_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(
                room=self.room,
                date_start=dt.date(2026, 6, 25),
                date_end=dt.date(2026, 6, 20),
            )

    def test_delete_room_deletes_bookings(self):
        Booking.objects.create(
            room=self.room, date_start=dt.date(2026, 6, 20), date_end=dt.date(2026, 6, 25)
        )

        self.room.delete()

        self.assertEqual(Booking.objects.count(), 0)
