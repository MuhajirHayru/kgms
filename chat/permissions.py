def can_access_room(user, room):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == "PARENT":
        return room.parent == user

    if user.role == "TEACHER":
        return room.teacher == user

    if user.role == "ACCOUNTANT":
        return room.accountant == user

    if user.role == "DIRECTOR":
        return room.director == user or user.is_superuser

    if user.role == "DRIVER":
        return room.driver == user

    return False
