from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="room_price_positive"),
        ]

    def __str__(self):
        return f"Room #{self.id} (${self.price})"


class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    date_start = models.DateField()
    date_end = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["room", "date_start"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_end__gt=models.F("date_start")),
                name="booking_end_after_start",
            ),
        ]

    def __str__(self):
        return f"Booking #{self.id}: room {self.room_id}, {self.date_start} – {self.date_end}"
