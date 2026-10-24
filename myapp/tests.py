from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ForumPost


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
        self.assertContains(response, "<title>Classmates</title>")
        self.assertContains(response, "All Discussions")
        self.assertContains(response, "How to implement dark mode in Tailwind CSS effortlessly")
        self.assertContains(response, 'id="menu-toggle"')
        self.assertContains(response, 'id="site-menu"')
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
        self.assertContains(response, "<title>Classmates | Calendar</title>")
        self.assertContains(response, 'id="menu-toggle"')
        self.assertContains(response, f'href="{reverse("home")}"', html=False)

    def test_menu_is_available_on_login_and_signup_pages(self):
        for url in (reverse("login"), reverse("signup")):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="menu-toggle"')
                self.assertContains(response, f'href="{reverse("calendar")}"', html=False)

    def test_authenticated_user_can_publish_forum_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {"title": "Study group", "content": "Anyone interested in meeting this week?"},
        )

        self.assertRedirects(response, reverse("home"))
        post = ForumPost.objects.get()
        self.assertEqual(post.title, "Study group")
        self.assertEqual(post.content, "Anyone interested in meeting this week?")
        self.assertEqual(post.author, self.user)

        response = self.client.get(reverse("home"))
        self.assertContains(response, "Study group")
        self.assertContains(response, "Anyone interested in meeting this week?")
        self.assertContains(response, f"Posted by {self.user.username}")

    def test_invalid_forum_post_is_not_published(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {"title": "", "content": "Post without a title"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ForumPost.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertNotContains(
            response,
            'id="post-form-container" class="hidden',
            html=False,
        )

    def test_anonymous_user_cannot_publish_forum_post(self):
        response = self.client.post(
            reverse("home"),
            {"title": "Study group", "content": "Let's meet."},
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )
        self.assertEqual(ForumPost.objects.count(), 0)

    def test_logout_returns_to_login_page(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
