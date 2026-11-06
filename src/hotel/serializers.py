from rest_framework import serializers

from hotel.models import Booking, Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "description", "price", "created_at"]


class BookingSerializer(serializers.ModelSerializer):
    room_id = serializers.PrimaryKeyRelatedField(source="room", queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ["id", "room_id", "date_start", "date_end"]
        extra_kwargs = {
            "date_start": {"input_formats": ["%Y-%m-%d"]},
            "date_end": {"input_formats": ["%Y-%m-%d"]},
        }

    def validate(self, attrs):
        if attrs["date_end"] <= attrs["date_start"]:
            raise serializers.ValidationError({"date_end": "date_end must be after date_start"})
        return attrs


class BookingListSerializer(serializers.ModelSerializer):
    booking_id = serializers.ReadOnlyField(source="id")

    class Meta:
        model = Booking
        fields = ["booking_id", "date_start", "date_end"]


class BookingListQuerySerializer(serializers.Serializer):
    room_id = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
