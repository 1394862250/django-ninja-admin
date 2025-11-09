import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.notification.model import Notification


class NotificationAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="regular", email="regular@example.com", password="pass1234"
        )
        self.client.force_login(self.user)
        self.auth_header = {"HTTP_AUTHORIZATION": "Bearer testtoken"}

    def test_list_notifications_with_filters_and_pagination(self):
        Notification.objects.create(
            recipient=self.user,
            title="System Alert",
            body="Check your system",
            category="system",
            status=Notification.STATUS.pending,
            priority=Notification.PRIORITY.medium,
        )
        Notification.objects.create(
            recipient=self.user,
            title="System Alert 2",
            body="Another alert",
            category="system",
            status=Notification.STATUS.sent,
            priority=Notification.PRIORITY.low,
        )
        Notification.objects.create(
            recipient=self.user,
            title="Marketing",
            body="A promo",
            category="marketing",
            status=Notification.STATUS.sent,
            priority=Notification.PRIORITY.low,
        )

        response = self.client.get(
            "/api/notifications",
            {"category": "system", "page_size": 1, "page": 1},
            **self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["pagination"]["total_count"], 2)
        self.assertEqual(len(payload["data"]["results"]), 1)
        self.assertEqual(payload["data"]["results"][0]["category"], "system")

    def test_unread_count_and_mark_read(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Unread",
            body="Needs attention",
            category="system",
            status=Notification.STATUS.pending,
            priority=Notification.PRIORITY.medium,
        )

        unread_response = self.client.get(
            "/api/notifications/unread-count",
            **self.auth_header,
        )

        self.assertEqual(unread_response.status_code, 200)
        self.assertEqual(unread_response.json()["data"]["count"], 1)

        mark_response = self.client.post(
            f"/api/notifications/mark-read/{notification.id}",
            **self.auth_header,
        )

        self.assertEqual(mark_response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

        unread_response_after = self.client.get(
            "/api/notifications/unread-count",
            **self.auth_header,
        )
        self.assertEqual(unread_response_after.json()["data"]["count"], 0)

    def test_bulk_mark_notifications_read(self):
        first = Notification.objects.create(
            recipient=self.user,
            title="First",
            body="First body",
            category="system",
            status=Notification.STATUS.pending,
            priority=Notification.PRIORITY.low,
        )
        second = Notification.objects.create(
            recipient=self.user,
            title="Second",
            body="Second body",
            category="system",
            status=Notification.STATUS.pending,
            priority=Notification.PRIORITY.low,
        )

        response = self.client.post(
            "/api/notifications/mark-read-bulk",
            data=json.dumps({"notification_ids": [first.id, second.id]}),
            content_type="application/json",
            **self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["updated"], 2)
        self.assertTrue(Notification.objects.filter(id=first.id, is_read=True).exists())
        self.assertTrue(Notification.objects.filter(id=second.id, is_read=True).exists())

    def test_create_notification_requires_staff(self):
        recipient = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="pass1234"
        )

        payload = {
            "recipient_id": recipient.id,
            "title": "Staff message",
            "body": "For staff only",
            "category": "system",
            "priority": Notification.PRIORITY.high,
            "status": Notification.STATUS.sent,
        }

        # Regular user should be forbidden
        forbidden_response = self.client.post(
            "/api/notifications",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(forbidden_response.status_code, 403)

        # Promote to staff and try again
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        staff_response = self.client.post(
            "/api/notifications",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_header,
        )

        self.assertEqual(staff_response.status_code, 201)
        response_data = staff_response.json()
        self.assertTrue(response_data["success"])
        created_id = response_data["data"]["id"]
        self.assertTrue(Notification.objects.filter(id=created_id, recipient=recipient).exists())

    def test_delete_notification(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Delete me",
            body="To be removed",
            category="system",
            status=Notification.STATUS.pending,
            priority=Notification.PRIORITY.medium,
        )

        response = self.client.delete(
            f"/api/notifications/{notification.id}",
            **self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())
