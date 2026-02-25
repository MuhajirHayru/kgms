from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Message


class UnreadMessageCountView(APIView):

    def get(self, request):
        count = Message.objects.filter(
            room__parent=request.user,
            is_read=False
        ).count()

        return Response({"unread_count": count})
    

class RoomUnreadCount(APIView):

    def get(self, request, room_id):

        count = Message.objects.filter(
            room_id=room_id,
            is_read=False
        ).exclude(sender=request.user).count()

        return Response({"unread": count})