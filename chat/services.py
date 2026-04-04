from django.db.models import Q

from accounts.models import User
from transport.models import BusAssignment

from .models import ChatRoom, Message


def _find_or_create_room(**kwargs):
    room = ChatRoom.objects.filter(**kwargs).order_by("id").first()
    if room:
        return room
    return ChatRoom.objects.create(**kwargs)


def _director_users():
    return User.objects.filter(Q(role="DIRECTOR") | Q(is_superuser=True)).distinct()


def _accountant_users():
    return User.objects.filter(role="ACCOUNTANT").distinct()


def create_parent_teacher_room(student):
    if not student.parent or not student.class_teacher_id or not student.class_teacher.user_id:
        return None

    return _find_or_create_room(
        room_type="PARENT_TEACHER",
        parent=student.parent,
        teacher=student.class_teacher.user,
        student=student,
    )


def ensure_parent_staff_rooms(parent):
    rooms = []
    for director in _director_users():
        room = _find_or_create_room(
            room_type="PARENT_ADMIN",
            parent=parent,
            director=director,
        )
        rooms.append(room)

    for accountant in _accountant_users():
        room = _find_or_create_room(
            room_type="PARENT_ACCOUNTANT",
            parent=parent,
            accountant=accountant,
        )
        rooms.append(room)
    return rooms


def ensure_parent_rooms(parent):
    rooms = ensure_parent_staff_rooms(parent)
    students = parent.children.select_related("class_teacher__user").all()
    for student in students:
        room = create_parent_teacher_room(student)
        if room:
            rooms.append(room)
    return rooms


def ensure_driver_staff_rooms(driver_user):
    rooms = []
    for director in _director_users():
        room = _find_or_create_room(
            room_type="DRIVER_ADMIN",
            driver=driver_user,
            director=director,
        )
        rooms.append(room)

    for accountant in _accountant_users():
        room = _find_or_create_room(
            room_type="DRIVER_ACCOUNTANT",
            driver=driver_user,
            accountant=accountant,
        )
        rooms.append(room)
    return rooms


def ensure_driver_parent_room(student, driver_user):
    if not student.parent:
        return None
    room = _find_or_create_room(
        room_type="DRIVER_PARENT",
        driver=driver_user,
        parent=student.parent,
        student=student,
    )
    return room


def ensure_driver_parent_rooms_for_driver(driver_user):
    rooms = []
    assignments = (
        BusAssignment.objects.filter(bus__driver__user=driver_user)
        .select_related("student", "student__parent")
        .distinct()
    )
    for assignment in assignments:
        room = ensure_driver_parent_room(assignment.student, driver_user)
        if room:
            rooms.append(room)
    return rooms


def ensure_driver_rooms(driver_user):
    rooms = ensure_driver_staff_rooms(driver_user)
    rooms.extend(ensure_driver_parent_rooms_for_driver(driver_user))
    return rooms


def ensure_staff_rooms(user):
    rooms = []
    if user.role == "ACCOUNTANT":
        parents = User.objects.filter(role="PARENT").distinct()
        for parent in parents:
            room = _find_or_create_room(
                room_type="PARENT_ACCOUNTANT",
                parent=parent,
                accountant=user,
            )
            rooms.append(room)

        assignments = (
            BusAssignment.objects.select_related("student", "student__parent", "bus__driver__user")
            .filter(bus__driver__isnull=False)
            .distinct()
        )
        for assignment in assignments:
            room = _find_or_create_room(
                room_type="DRIVER_ACCOUNTANT",
                driver=assignment.bus.driver.user,
                accountant=user,
            )
            rooms.append(room)

    if user.role == "DIRECTOR" or user.is_superuser:
        parents = User.objects.filter(role="PARENT").distinct()
        for parent in parents:
            room = _find_or_create_room(
                room_type="PARENT_ADMIN",
                parent=parent,
                director=user,
            )
            rooms.append(room)

        assignments = (
            BusAssignment.objects.select_related("student", "student__parent", "bus__driver__user")
            .filter(bus__driver__isnull=False)
            .distinct()
        )
        for assignment in assignments:
            room = _find_or_create_room(
                room_type="DRIVER_ADMIN",
                driver=assignment.bus.driver.user,
                director=user,
            )
            rooms.append(room)
    return rooms


def ensure_rooms_for_user(user):
    if user.role == "PARENT":
        return ensure_parent_rooms(user)
    if user.role == "DRIVER":
        return ensure_driver_rooms(user)
    if user.role in {"ACCOUNTANT", "DIRECTOR"} or user.is_superuser:
        return ensure_staff_rooms(user)
    return []


def create_system_message(room, sender, content):
    return Message.objects.create(
        room=room,
        sender=sender,
        content=content,
    )


def broadcast_driver_alert(driver_user, bus, alert_type, message):
    driver_label = driver_user.full_name or driver_user.phone_number
    content = f"Driver alert ({alert_type}) from {driver_label} for bus {bus.bus_number}: {message}".strip()

    recipients = []
    for room in ensure_driver_staff_rooms(driver_user):
        recipients.append(create_system_message(room, driver_user, content))

    assignments = (
        BusAssignment.objects.filter(bus=bus)
        .select_related("student", "student__parent")
        .distinct()
    )
    for assignment in assignments:
        room = ensure_driver_parent_room(assignment.student, driver_user)
        if room:
            recipients.append(create_system_message(room, driver_user, content))
    return recipients
