from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import DriverProfile, User
from chat.models import ChatRoom, Message
from employees.models import Employee
from students.models import Student
from transport.models import Bus, BusAssignment, DriverAlert, Route


class ChatApiTests(APITestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            phone_number="0912000001",
            password="pass1234",
            role="PARENT",
            full_name="Parent Chat",
        )
        self.teacher = User.objects.create_user(
            phone_number="0912000002",
            password="pass1234",
            role="TEACHER",
            full_name="Teacher Chat",
        )
        self.accountant = User.objects.create_user(
            phone_number="0912000003",
            password="pass1234",
            role="ACCOUNTANT",
            full_name="Accountant Chat",
        )
        self.director = User.objects.create_user(
            phone_number="0912000005",
            password="pass1234",
            role="DIRECTOR",
            full_name="Director Chat",
        )
        self.driver = User.objects.create_user(
            phone_number="0912000006",
            password="pass1234",
            role="DRIVER",
            full_name="Driver Chat",
        )
        self.other_parent = User.objects.create_user(
            phone_number="0912000007",
            password="pass1234",
            role="PARENT",
            full_name="Other Parent",
        )
        self.driver_profile = DriverProfile.objects.create(user=self.driver, license_number="DR-123")
        self.teacher_employee = Employee.objects.create(user=self.teacher, role="TEACHER", salary="1000.00")
        self.route = Route.objects.create(name="Route A")
        self.bus = Bus.objects.create(
            bus_number="BUS-01",
            plate_number="AA-12345",
            capacity=30,
            driver=self.driver_profile,
            route=self.route,
        )
        self.student = Student.objects.create(
            first_name="Kid",
            last_name="One",
            dob="2018-01-01",
            gender="M",
            category="KG",
            grade_level="KG1",
            transport="BUS",
            parent=self.parent,
            class_teacher=self.teacher_employee,
            class_name="KG1A",
        )
        self.room = ChatRoom.objects.create(
            room_type="PARENT_TEACHER",
            parent=self.parent,
            teacher=self.teacher,
            student=self.student,
        )

    def test_room_list_returns_only_user_rooms(self):
        ChatRoom.objects.create(
            room_type="PARENT_ACCOUNTANT",
            parent=self.other_parent,
            accountant=self.accountant,
        )
        self.client.force_authenticate(self.parent)

        response = self.client.get(reverse("chat-room-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_ids = {item["id"] for item in response.data}
        self.assertIn(self.room.id, room_ids)
        self.assertFalse(ChatRoom.objects.filter(id__in=room_ids, parent=self.other_parent).exists())

    def test_message_create_requires_room_membership(self):
        self.client.force_authenticate(self.other_parent)

        response = self.client.post(
            reverse("chat-room-messages", kwargs={"room_id": self.room.id}),
            data={"content": "Hello"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_message_create_saves_message_for_room_member(self):
        self.client.force_authenticate(self.parent)

        response = self.client.post(
            reverse("chat-room-messages", kwargs={"room_id": self.room.id}),
            data={"content": "Hello teacher"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Message.objects.filter(room=self.room, sender=self.parent, content="Hello teacher").exists())

    def test_unread_counts_are_scoped_to_accessible_rooms(self):
        Message.objects.create(room=self.room, sender=self.teacher, content="Unread 1")
        Message.objects.create(room=self.room, sender=self.teacher, content="Unread 2")
        self.client.force_authenticate(self.parent)

        response = self.client.get(reverse("chat-unread-count"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 2)

    def test_room_list_marks_messages_read_when_opened(self):
        Message.objects.create(room=self.room, sender=self.teacher, content="Please review")
        self.client.force_authenticate(self.parent)

        response = self.client.get(reverse("chat-room-messages", kwargs={"room_id": self.room.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["content"], "Please review")
        self.assertEqual(Message.objects.get(room=self.room).is_read, True)

    def test_room_unread_count_denies_non_member(self):
        self.client.force_authenticate(self.other_parent)

        response = self.client.get(reverse("chat-room-unread-count", kwargs={"room_id": self.room.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_parent_room_list_includes_accountant_and_admin_rooms(self):
        self.client.force_authenticate(self.parent)

        response = self.client.get(reverse("chat-room-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = {item["room_type"] for item in response.data}
        self.assertIn("PARENT_ACCOUNTANT", room_types)
        self.assertIn("PARENT_ADMIN", room_types)
        self.assertNotIn("DRIVER_PARENT", room_types)

    def test_bus_assignment_creates_driver_parent_room(self):
        BusAssignment.objects.create(student=self.student, bus=self.bus)

        self.assertTrue(
            ChatRoom.objects.filter(
                room_type="DRIVER_PARENT",
                parent=self.parent,
                driver=self.driver,
                student=self.student,
            ).exists()
        )

    def test_driver_alert_broadcasts_only_to_assigned_family_and_staff(self):
        BusAssignment.objects.create(student=self.student, bus=self.bus)
        self.client.force_authenticate(self.driver)

        response = self.client.post(
            reverse("driver-alert-create"),
            data={
                "bus": self.bus.id,
                "alert_type": "DELAY",
                "message": "Bus is delayed because of traffic.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DriverAlert.objects.filter(driver=self.driver_profile, bus=self.bus).exists())
        self.assertTrue(ChatRoom.objects.filter(room_type="DRIVER_PARENT", parent=self.parent, driver=self.driver).exists())
        self.assertTrue(ChatRoom.objects.filter(room_type="DRIVER_ACCOUNTANT", accountant=self.accountant, driver=self.driver).exists())
        self.assertTrue(ChatRoom.objects.filter(room_type="DRIVER_ADMIN", director=self.director, driver=self.driver).exists())
        self.assertFalse(ChatRoom.objects.filter(room_type="DRIVER_PARENT", parent=self.other_parent, driver=self.driver).exists())
        self.assertEqual(
            Message.objects.filter(room__room_type="DRIVER_PARENT", room__parent=self.parent, sender=self.driver).count(),
            1,
        )
