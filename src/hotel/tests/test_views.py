import datetime as dt

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from hotel.models import Booking, Room


class RoomCreateApiTest(APITestCase):
    def test_create_room(self):
        resp = self.client.post(reverse("room-list"), {"description": "Standard", "price": "3500"})

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        room_id = resp.json()["room_id"]
        self.assertTrue(Room.objects.filter(id=room_id).exists())

    def test_create_room_invalid_price(self):
        resp = self.client.post(reverse("room-list"), {"description": "Standard", "price": "abc"})

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.json())
        self.assertEqual(Room.objects.count(), 0)

    def test_create_room_non_positive_price(self):
        for price in ["-100", "0", "0.00"]:
            with self.subTest(price=price):
                resp = self.client.post(
                    reverse("room-list"), {"description": "Standard", "price": price}
                )

                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("price", resp.json())

        self.assertEqual(Room.objects.count(), 0)


class RoomListApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        for price in ["3000.00", "1000.00", "2000.00"]:
            Room.objects.create(description=f"Room {price}", price=price)

    def test_list_ordered_by_price_asc(self):
        resp = self.client.get(reverse("room-list"), {"ordering": "price"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        prices = [room["price"] for room in resp.json()["results"]]
        self.assertEqual(prices, ["1000.00", "2000.00", "3000.00"])

    def test_list_ordered_by_price_desc(self):
        resp = self.client.get(reverse("room-list"), {"ordering": "-price"})

        prices = [room["price"] for room in resp.json()["results"]]
        self.assertEqual(prices, ["3000.00", "2000.00", "1000.00"])


class RoomListPaginationApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Room.objects.bulk_create(Room(description=f"Room {i}", price="1000.00") for i in range(25))

    def test_first_page(self):
        resp = self.client.get(reverse("room-list"))

        data = resp.json()
        self.assertEqual(data["count"], 25)
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_page_size_param(self):
        resp = self.client.get(reverse("room-list"), {"page_size": 10, "page": 3})

        data = resp.json()
        self.assertEqual(len(data["results"]), 5)
        self.assertIsNone(data["next"])

    def test_ordering_has_id_tiebreaker(self):

        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("room-list"), {"ordering": "-price"})

        select_sql = next(q["sql"] for q in ctx.captured_queries if "LIMIT" in q["sql"])
        self.assertIn('ORDER BY "hotel_room"."price" DESC, "hotel_room"."id" ASC', select_sql)


class RoomDeleteApiTest(APITestCase):
    def test_delete_room(self):
        room = Room.objects.create(description="Test room", price="1000.00")

        resp = self.client.delete(reverse("room-detail", kwargs={"pk": room.id}))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), {"deleted_room_id": room.id})
        self.assertFalse(Room.objects.filter(id=room.id).exists())

    def test_delete_missing_room(self):
        resp = self.client.delete(reverse("room-detail", kwargs={"pk": 999999}))

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class BookingCreateApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(description="Test room", price="1000.00")

    def post_booking(self, room_id, date_start, date_end):
        return self.client.post(
            reverse("booking-list"),
            {"room_id": room_id, "date_start": date_start, "date_end": date_end},
        )

    def test_create_booking(self):
        resp = self.post_booking(self.room.id, "2026-06-20", "2026-06-25")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("booking_id", resp.json())

    def test_overlapping_booking_conflict(self):
        self.post_booking(self.room.id, "2026-06-20", "2026-06-25")

        resp = self.post_booking(self.room.id, "2026-06-23", "2026-06-27")

        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Booking.objects.count(), 1)

    def test_invalid_input_rejected(self):
        cases = [
            (999999, "2026-06-20", "2026-06-25", "room_id"),
            (None, "2026-02-30", "2026-03-02", "date_start"),
            (None, "20.06.2026", "2026-06-25", "date_start"),
            (None, "2026-06-25", "2026-06-20", "date_end"),
        ]
        for room_id, date_start, date_end, error_field in cases:
            with self.subTest(error_field=error_field, date_start=date_start):
                resp = self.post_booking(room_id or self.room.id, date_start, date_end)

                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(error_field, resp.json())

        self.assertEqual(Booking.objects.count(), 0)


class BookingListApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(description="Test room", price="1000.00")
        for start in [dt.date(2026, 7, 10), dt.date(2026, 6, 1), dt.date(2026, 6, 20)]:
            Booking.objects.create(
                room=cls.room, date_start=start, date_end=start + dt.timedelta(days=2)
            )

    def test_list_sorted_by_date_start(self):
        resp = self.client.get(reverse("booking-list"), {"room_id": self.room.id})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        starts = [b["date_start"] for b in resp.json()["results"]]
        self.assertEqual(starts, ["2026-06-01", "2026-06-20", "2026-07-10"])

    def test_list_item_format(self):
        resp = self.client.get(reverse("booking-list"), {"room_id": self.room.id})

        self.assertEqual(
            set(resp.json()["results"][0].keys()), {"booking_id", "date_start", "date_end"}
        )

    def test_list_without_room_id(self):
        resp = self.client.get(reverse("booking-list"))

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class BookingDeleteApiTest(APITestCase):
    def test_delete_booking(self):
        room = Room.objects.create(description="Test room", price="1000.00")
        booking = Booking.objects.create(
            room=room, date_start=dt.date(2026, 6, 20), date_end=dt.date(2026, 6, 25)
        )

        resp = self.client.delete(reverse("booking-detail", kwargs={"pk": booking.id}))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
