from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SignUpTests(TestCase):
    def test_signup_page_renders_form_and_login_link(self):
        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, reverse("login"))
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')

    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "password1": "A-safe-test-password-123!",
                "password2": "A-safe-test-password-123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertTrue(
            get_user_model().objects.filter(username="newmember").exists()
        )

    def test_signup_shows_validation_errors(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "password1": "short",
                "password2": "different",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="newmember").exists()
        )
        self.assertContains(response, "The two password fields didn’t match.")
