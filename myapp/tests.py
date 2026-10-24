from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ForumPost, Message


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


class ChatTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.sender = user_model.objects.create_user(
            username="sender",
            password="A-safe-test-password-123",
        )
        self.recipient = user_model.objects.create_user(
            username="recipient",
            password="A-safe-test-password-123",
        )

    def test_chat_page_lists_other_users_and_shows_shared_menu(self):
        self.client.force_login(self.sender)

        response = self.client.get(reverse("chat"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat.html")
        self.assertContains(response, self.recipient.username)
        self.assertContains(response, 'id="menu-toggle"')
        self.assertContains(response, "Your messages")

    def test_user_can_send_and_read_private_messages(self):
        self.client.force_login(self.sender)
        url = reverse(
            "chat_conversation",
            kwargs={"username": self.recipient.username},
        )

        response = self.client.post(
            reverse(
                "send_message",
                kwargs={"username": self.recipient.username},
            ),
            {"content": "Hello there"},
        )

        self.assertRedirects(response, url)
        message = Message.objects.get()
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.recipient)
        self.assertEqual(message.content, "Hello there")

        response = self.client.get(url)
        self.assertContains(response, "Hello there")
        self.assertContains(response, "Private conversation")

    def test_messages_are_visible_to_both_conversation_participants(self):
        Message.objects.create(
            sender=self.sender,
            receiver=self.recipient,
            content="Only these two users can see this.",
        )
        self.client.force_login(self.recipient)

        response = self.client.get(
            reverse(
                "chat_conversation",
                kwargs={"username": self.sender.username},
            )
        )

        self.assertContains(response, "Only these two users can see this.")
        self.assertContains(response, "sender")

    def test_message_is_not_sent_when_content_is_empty(self):
        self.client.force_login(self.sender)
        url = reverse(
            "chat_conversation",
            kwargs={"username": self.recipient.username},
        )

        response = self.client.post(
            reverse(
                "send_message",
                kwargs={"username": self.recipient.username},
            ),
            {"content": "   "},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        self.assertEqual(Message.objects.count(), 0)
        response = self.client.get(url)
        self.assertContains(response, "Write a message before sending.")

    def test_chat_requires_login_and_rejects_self_conversation(self):
        conversation_url = reverse(
            "chat_conversation",
            kwargs={"username": self.recipient.username},
        )
        response = self.client.get(reverse("chat"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('chat')}",
        )

        self.client.force_login(self.sender)
        self.assertEqual(
            self.client.get(
                reverse(
                    "chat_conversation",
                    kwargs={"username": self.sender.username},
                )
            ).status_code,
            404,
        )
        self.assertEqual(self.client.get(conversation_url).status_code, 200)
