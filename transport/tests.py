from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import DriverProfile, User
from employees.models import Employee
from students.models import Student
from transport.models import Bus, BusAssignment, Route


class BusAssignmentApiTests(APITestCase):
    def setUp(self):
        self.director = User.objects.create_user(
            phone_number="0913000001",
            password="pass1234",
            role="DIRECTOR",
            full_name="Director Transport",
        )
        self.driver = User.objects.create_user(
            phone_number="0913000002",
            password="pass1234",
            role="DRIVER",
            full_name="Driver Transport",
        )
        self.parent = User.objects.create_user(
            phone_number="0913000003",
            password="pass1234",
            role="PARENT",
            full_name="Parent Transport",
        )
        self.teacher = User.objects.create_user(
            phone_number="0913000004",
            password="pass1234",
            role="TEACHER",
            full_name="Teacher Transport",
        )
        self.driver_profile = DriverProfile.objects.create(user=self.driver, license_number="DRV-200")
        self.teacher_employee = Employee.objects.create(user=self.teacher, role="TEACHER", salary="1000.00")
        self.route = Route.objects.create(name="North Route")
        self.bus = Bus.objects.create(
            bus_number="BUS-10",
            plate_number="AA-77777",
            capacity=25,
            driver=self.driver_profile,
            route=self.route,
        )
        self.student = Student.objects.create(
            first_name="Beki",
            last_name="Kid",
            dob="2018-02-02",
            gender="F",
            category="KG",
            grade_level="KG2",
            transport="BUS",
            address="Main area",
            emergency_contact="0913555555",
            parent=self.parent,
            class_teacher=self.teacher_employee,
            class_name="KG2A",
        )

    def test_director_can_allocate_student_to_specific_bus(self):
        self.client.force_authenticate(self.director)

        response = self.client.post(
            reverse("bus-assignment-list-create"),
            data={"student": self.student.id, "bus": self.bus.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BusAssignment.objects.filter(student=self.student, bus=self.bus).exists())

    def test_non_director_cannot_allocate_student_to_bus(self):
        self.client.force_authenticate(self.driver)

        response = self.client.post(
            reverse("bus-assignment-list-create"),
            data={"student": self.student.id, "bus": self.bus.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_only_have_one_current_bus_assignment(self):
        BusAssignment.objects.create(student=self.student, bus=self.bus)
        another_route = Route.objects.create(name="South Route")
        another_bus = Bus.objects.create(
            bus_number="BUS-11",
            plate_number="AA-88888",
            capacity=25,
            driver=self.driver_profile,
            route=another_route,
        )
        self.client.force_authenticate(self.director)

        response = self.client.post(
            reverse("bus-assignment-list-create"),
            data={"student": self.student.id, "bus": another_bus.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("student", response.data)
