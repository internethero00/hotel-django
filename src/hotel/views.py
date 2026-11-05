from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from . import services
from .models import Booking, Room
from .serializers import (
    BookingListQuerySerializer,
    BookingListSerializer,
    BookingSerializer,
    RoomSerializer,
)


class BookingConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Room is already booked for these dates."
    default_code = "booking_conflict"


class JsonListCreateAPIView(generics.ListCreateAPIView):
    response_key = "id"

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {self.response_key: response.data["id"]}
        return response


class JsonDestroyAPIView(generics.DestroyAPIView):
    response_key = "deleted_id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        return Response({self.response_key: instance_id}, status=status.HTTP_200_OK)


class RoomListCreateView(JsonListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["price", "created_at"]
    ordering = ["created_at"]
    response_key = "room_id"


class RoomDetailView(JsonDestroyAPIView):
    queryset = Room.objects.all()
    response_key = "deleted_room_id"


class BookingListCreateView(JsonListCreateAPIView):
    response_key = "booking_id"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BookingSerializer
        return BookingListSerializer

    def get_queryset(self):
        query = BookingListQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        room = query.validated_data["room_id"]
        return room.bookings.order_by("date_start")

    def perform_create(self, serializer):
        try:
            serializer.instance = services.booking_create(**serializer.validated_data)
        except services.BookingConflictError as e:
            raise BookingConflict(str(e)) from e


class BookingDetailView(JsonDestroyAPIView):
    queryset = Booking.objects.all()
    response_key = "deleted_booking_id"
