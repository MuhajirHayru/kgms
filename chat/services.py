from .models import ChatRoom
from students.models import Student


def create_parent_teacher_room(student):

    parent = student.parent
    teacher = student.class_teacher.user

    room, created = ChatRoom.objects.get_or_create(
        room_type='PARENT_TEACHER',
        parent=parent,
        teacher=teacher,
        student=student
    )

    return room