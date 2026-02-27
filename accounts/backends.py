from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


UserModel = get_user_model()


class PhoneOrSuperuserUsernameBackend(ModelBackend):
    """
    Auth rules:
    - All users can log in with phone_number + password.
    - Superusers can also log in with username + password.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("phone_number")
        if not identifier or password is None:
            return None

        # Primary path: phone login for all users.
        try:
            user = UserModel.objects.get(phone_number=identifier)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            pass

        # Secondary path: username login only for superusers.
        try:
            user = UserModel.objects.get(username=identifier, is_superuser=True)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            return None

        return None
