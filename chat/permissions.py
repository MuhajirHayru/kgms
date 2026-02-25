def can_access_room(user, room):

    if user.role == "PARENT":
        return room.parent == user

    if user.role == "TEACHER":
        return room.teacher == user

    if user.role == "ACCOUNTANT":
        return room.accountant == user

    if user.role == "DRIVER":
        return room.driver == user

    return False