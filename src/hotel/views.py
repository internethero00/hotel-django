from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RoomSerializer


class RoomCreateView(APIView):
    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        return Response({"room_id": room.id}, status=status.HTTP_201_CREATED)
