"""
Tests for the account credential update API.
"""
import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class UpdateCredentialsAPITestCase(TestCase):
    """Tests covering the /api/update-credentials endpoint."""

    endpoint = "/api/update-credentials"

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Initial1!"
        )
        self.existing_user = User.objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            password="Existing1!"
        )

    def post_update(self, payload, user=None):
        client = Client()
        if user:
            client.force_login(user)
        return client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def assert_error_response(self, response, status_code, expected_message):
        self.assertEqual(response.status_code, status_code)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], expected_message)
        return data

    def assert_success_response(self, response, expected_message):
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["message"], expected_message)
        return data


    # ---------- USERNAME TESTS ----------
    def test_username_too_short(self):
        response = self.post_update({"new_username": "ab"}, user=self.user)
        self.assert_error_response(
            response, 400, "Username must be at least 3 characters long"
        )

    def test_username_already_exists(self):
        response = self.post_update(
            {"new_username": "ExistingUser"}, user=self.user
        )
        self.assert_error_response(response, 400, "Username already exists")

    def test_username_update_success(self):
        payload = {"new_username": "updateduser"}
        response = self.post_update(payload, user=self.user)
        self.assert_success_response(
            response, "Credentials updated successfully. Please log in again."
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")

    # ---------- PASSWORD TESTS ----------
    def test_password_equals_username(self):
        response = self.post_update({"new_password": "testuser"}, user=self.user)
        self.assert_error_response(
            response, 400, "Password must not equal the username"
        )

    def test_password_contains_username(self):
        response = self.post_update(
            {"new_password": "TestUser123!"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must not contain the username"
        )

    def test_password_contains_reversed_username(self):
        reversed_username = self.user.username[::-1]
        response = self.post_update(
            {"new_password": f"{reversed_username}123!"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must not contain the reversed username"
        )

    def test_password_missing_uppercase(self):
        response = self.post_update(
            {"new_password": "lowercase1!"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must contain at least one uppercase letter"
        )

    def test_password_missing_lowercase(self):
        response = self.post_update(
            {"new_password": "UPPERCASE1!"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must contain at least one lowercase letter"
        )

    def test_password_missing_number(self):
        response = self.post_update(
            {"new_password": "NoNumber!"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must contain at least one number"
        )

    def test_password_missing_special_character(self):
        response = self.post_update(
            {"new_password": "NoSpecial1A"}, user=self.user
        )
        self.assert_error_response(
            response, 400, "Password must contain at least one special character"
        )

    def test_password_too_short(self):
        response = self.post_update({"new_password": "Aa1!"}, user=self.user)
        self.assert_error_response(
            response, 400, "Password must be at least 8 characters long"
        )

    def test_password_update_success(self):
        valid_password = "Valid1!Pass"
        response = self.post_update(
            {"new_password": valid_password}, user=self.user
        )
        self.assert_success_response(
            response, "Credentials updated successfully. Please log in again."
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(valid_password))

    # ---------- COMBINED ----------
    def test_username_and_password_update_combined(self):
        payload = {
            "new_username": "combineduser",
            "new_password": "Combined1!"
        }
        response = self.post_update(payload, user=self.user)
        self.assert_success_response(
            response, "Credentials updated successfully. Please log in again."
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "combineduser")
        self.assertTrue(self.user.check_password("Combined1!"))
