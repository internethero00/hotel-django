from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Room
from .serializers import RoomSerializer


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
