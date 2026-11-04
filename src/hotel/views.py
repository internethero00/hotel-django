from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Booking, Room
from .serializers import (
    BookingListQuerySerializer,
    BookingListSerializer,
    BookingSerializer,
    RoomSerializer,
)


class JsonDestroyAPIView(generics.DestroyAPIView):
    response_key = "deleted_id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        return Response({self.response_key: instance_id}, status=status.HTTP_200_OK)


class RoomCreateView(APIView):
    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        return Response({"room_id": room.id}, status=status.HTTP_201_CREATED)


class RoomListView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["price", "created_at"]
    ordering = ["created_at"]


class RoomDeleteView(JsonDestroyAPIView):
    queryset = Room.objects.all()
    response_key = "deleted_room_id"


class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = services.booking_create(**serializer.validated_data)
        except services.BookingConflictError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response({"booking_id": booking.id}, status=status.HTTP_201_CREATED)


class BookingDeleteView(JsonDestroyAPIView):
    queryset = Booking.objects.all()
    response_key = "deleted_booking_id"


class BookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer

    def get_queryset(self):
        query = BookingListQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        room = query.validated_data["room_id"]
        return room.bookings.order_by("date_start")
