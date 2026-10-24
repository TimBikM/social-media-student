from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="A-safe-test-password-123",
        )

    def test_login_page_uses_django_auth_template(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, "{% csrf_token %}")
        self.assertNotContains(response, "{{ form.non_field_errors }}")
        self.assertNotContains(response, "{% csrf_token %}")
        self.assertNotContains(response, "{% if form.non_field_errors %}")

    def test_invalid_credentials_show_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "incorrect"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")
        self.assertNotContains(response, f'value="{self.user.username}"')
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_successful_login_redirects_to_authenticated_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "A-safe-test-password-123"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_remember_me_keeps_persistent_session(self):
        self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": "A-safe-test-password-123",
                "remember-me": "1",
            },
        )

        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )

    def test_authenticated_home_displays_forum(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>DevForum</title>")
        self.assertContains(response, "All Discussions")
        self.assertContains(response, "How to implement dark mode in Tailwind CSS effortlessly")
        self.assertContains(response, f'href="{reverse("calendar")}"', html=False)
        self.assertContains(response, "Chat")
        self.assertContains(
            response,
            f'action="{reverse("logout")}"',
            html=False,
        )

    def test_calendar_route_displays_existing_calendar(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("calendar"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "calendar.html")
        self.assertContains(response, "<title>Local Calendar</title>")

    def test_logout_returns_to_login_page(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
