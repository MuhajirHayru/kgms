from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatRoom, Message
from .permissions import can_access_room
from .serializers import ChatRoomSerializer, MessageSerializer
from .services import ensure_rooms_for_user


def _rooms_for_user(user):
    return ChatRoom.objects.select_related(
        "parent",
        "teacher",
        "accountant",
        "director",
        "driver",
        "student",
    ).filter(
        Q(parent=user) |
        Q(teacher=user) |
        Q(accountant=user) |
        Q(director=user) |
        Q(driver=user)
    ).distinct()


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ensure_rooms_for_user(self.request.user)
        return _rooms_for_user(self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_room(self):
        room = ChatRoom.objects.select_related("parent", "teacher", "accountant", "director", "driver").filter(
            pk=self.kwargs["room_id"]
        ).first()
        if room is None or not can_access_room(self.request.user, room):
            return None
        return room

    def get_queryset(self):
        room = self.get_room()
        if room is None:
            return Message.objects.none()
        return Message.objects.filter(room=room).select_related("sender")

    def list(self, request, *args, **kwargs):
        room = self.get_room()
        if room is None:
            return Response({"error": "Room not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        room = self.get_room()
        if room is None:
            raise PermissionDenied("Room not found or access denied.")
        serializer.save(room=room, sender=self.request.user)


class UnreadMessageCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = _rooms_for_user(request.user)
        count = Message.objects.filter(
            room__in=rooms,
            is_read=False,
        ).exclude(sender=request.user).count()
        return Response({"unread_count": count})


class RoomUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        room = ChatRoom.objects.select_related("parent", "teacher", "accountant", "director", "driver").filter(pk=room_id).first()
        if room is None or not can_access_room(request.user, room):
            return Response({"error": "Room not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        count = Message.objects.filter(
            room_id=room_id,
            is_read=False,
        ).exclude(sender=request.user).count()
        return Response({"unread": count})


class MarkRoomReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        room = ChatRoom.objects.select_related("parent", "teacher", "accountant", "director", "driver").filter(pk=room_id).first()
        if room is None or not can_access_room(request.user, room):
            return Response({"error": "Room not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        updated = room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)
