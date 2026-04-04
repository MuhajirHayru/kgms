from django.urls import path

from .views import (
    ChatRoomListView,
    MarkRoomReadView,
    MessageListCreateView,
    RoomUnreadCountView,
    UnreadMessageCountView,
)

urlpatterns = [
    path("rooms/", ChatRoomListView.as_view(), name="chat-room-list"),
    path("rooms/<int:room_id>/messages/", MessageListCreateView.as_view(), name="chat-room-messages"),
    path("rooms/<int:room_id>/read/", MarkRoomReadView.as_view(), name="chat-room-read"),
    path("unread/", UnreadMessageCountView.as_view(), name="chat-unread-count"),
    path("rooms/<int:room_id>/unread/", RoomUnreadCountView.as_view(), name="chat-room-unread-count"),
]
