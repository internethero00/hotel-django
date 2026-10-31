from decimal import Decimal

from rest_framework import serializers

from hotel.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "description", "price", "created_at"]
        extra_kwargs = {"price": {"min_value": Decimal("0.01")}}
