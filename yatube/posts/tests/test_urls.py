from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text_post',
            group=cls.group
        )
        cls.url_template_auth = {
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html'
        }
        cls.url_template_guest = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/Test_user/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        cls.url_status_code_any = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/Test_user/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/': HTTPStatus.OK,
            '/post/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/group/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/profile/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        cls.url_status_code_guest = {
            '/create/': HTTPStatus.FOUND,
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.FOUND
        }
        cls.url_status_code_auth = {
            '/create/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.OK
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_anonymous(self):
        """Шаблон соответствует URL-адресу для анонимного пользователя."""
        for address, template in self.url_template_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_authorized(self):
        """Шаблон соответствует URL-адресу для авторизованного пользователя."""
        for address, template in (
            self.url_template_auth.items() and self.url_template_guest.items()
        ):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_anonymous(self):
        """URL-адрес соответствует ответу для анонимного пользователя."""
        for address, status in (
            self.url_status_code_any and self.url_status_code_guest.items()
        ):
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_url_exists_at_desired_location_authorized(self):
        """URL-адрес соответствует ответу для авторизованного пользователя."""
        for address, status in (
            self.url_status_code_any and self.url_status_code_auth.items()
        ):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)
