import shutil
import tempfile
from datetime import date

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='Test_user',
            first_name='Test',
            last_name='User')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text_post',
            group=cls.group,
            pub_date=date(2020, 2, 27),
            image=cls.uploaded
        )
        cls.group_other = Group.objects.create(
            title='test_group_other',
            slug='test_slug_other',
            description='test_description_other',
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'test_text_post')
        self.assertEqual(first_object.image, self.post.image)

    def test_group_post_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.title, 'test_group')
        self.assertEqual(first_object.group.slug, 'test_slug')
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        profile_full_name = first_object.author.get_full_name()
        self.assertEqual(
            ('Профайл пользователя ' + profile_full_name),
            'Профайл пользователя Test User')
        self.assertEqual(first_object.author.posts.count(), 1)
        self.assertEqual(profile_full_name, 'Test User')
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context.get('post')
        post_detail_title_0 = post.text[:30]
        self.assertEqual(post, self.post)
        self.assertEqual(post_detail_title_0, self.post.text[:30])
        self.assertEqual(post.author.posts.count(), 1)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        post = response.context.get('post')
        is_edit = True
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        self.assertEqual(post, self.post)
        self.assertEqual(is_edit, True)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_another_group(self):
        """Пост не попал в другую группу"""
        self.post_in_another_group = Post.objects.create(
            author=self.user,
            text='test_text_post_another',
            group=self.group_other,
            pub_date=date(2020, 2, 26)
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_other.slug})
        )
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.group.title, 'test_group')
        self.assertNotEqual(first_object.group.slug, 'test_slug')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='Test_user',
            first_name='Test',
            last_name='User')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.TEST_POST_PER_PAGE = 10
        cls.TEST_AMOUNT_POSTS = 13
        for i in range(cls.TEST_AMOUNT_POSTS):
            cls.post = Post.objects.create(
                author=cls.user,
                text='test_text_post №' + str(i),
                group=cls.group
            )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): 'posts/profile.html'}

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """На первой странице 10 постов"""
        for template in self.templates_pages_names:
            response = self.client.get(template)
            self.assertEqual(
                len(response.context['page_obj']), self.TEST_POST_PER_PAGE)

    def test_second_page_contains_three_records(self):
        """На второй странице 3 поста"""
        for template in self.templates_pages_names:
            AMOUNT_POSTS_SECOND_PAGE = (
                self.TEST_AMOUNT_POSTS % self.TEST_POST_PER_PAGE)
            response = self.client.get(template + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']), AMOUNT_POSTS_SECOND_PAGE)


class CahePageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='Test_user',
            first_name='Test',
            last_name='User')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text_post',
            group=cls.group,
            pub_date=date(2020, 3, 6),
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        """Страница index_page сохраняет в cache список постов."""
        form_data = {
            'text': 'Текст новго поста',
            'group': self.group.id,
        }
        response = self.authorized_client.get(reverse('posts:index'))
        content_before = response.content
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(reverse('posts:index'))
        content_after = response.content
        self.assertTrue(content_before == content_after)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_author = User.objects.create(
            username='Main Author',
            first_name='Test',
            last_name='User')
        cls.main_follower = User.objects.create(
            username='Main Follower',
            first_name='Test',
            last_name='User')
        cls.second_follower = User.objects.create(
            username='Second Follower',
            first_name='Test',
            last_name='User')
        cls.test_follow = Follow.objects.create(
            user=cls.main_follower,
            author=cls.main_author
        )
        cls.TEST_AMOUNT_POSTS = 5
        for i in range(cls.TEST_AMOUNT_POSTS):
            cls.post = Post.objects.create(
                author=cls.main_author,
                text='test_text_post №' + str(i),
            )

    def setUp(self):
        cache.clear()
        self.bloger = Client()
        self.bloger.force_login(self.main_author)
        self.follower = Client()
        self.follower.force_login(self.main_follower)
        self.follower_other = Client()
        self.follower_other.force_login(self.second_follower)

    def test_create_follow(self):
        """Создание подписки на блогера"""
        follow_count_before = Follow.objects.count()
        self.follower_other.get(reverse(
                'posts:profile_follow',
                kwargs={'username': self.main_author.username})
        )
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_before + 1, follow_count_after)

    def test_create_unfollow(self):
        """Удаление подписки на блогера"""
        follow_count_before = Follow.objects.count()
        self.follower.get(reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.main_author.username})
        )
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_before, follow_count_after + 1)

    def test_user_cannot_follow_himself(self):
        """Нельзя подписаться на самого себя"""
        follow_count_before = Follow.objects.count()
        self.bloger.get(reverse(
                'posts:profile_follow',
                kwargs={'username': self.main_author.username})
        )
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_before, follow_count_after)

    def test_new_post_in_correct_page(self):
        """Новый пост появляется в нужной ленте подписок"""
        response_follower = self.follower.get(reverse('posts:follow_index',))
        self.assertEqual(
            len(response_follower.context["page_obj"]), self.TEST_AMOUNT_POSTS)
        response_follower_other = self.follower_other.get(
            reverse('posts:follow_index',))
        self.assertEqual(len(response_follower_other.context["page_obj"]), 0)
        form_data = {
            'text': 'Текст новго поста',
        }
        self.bloger.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response_follower = self.follower.get(reverse('posts:follow_index',))
        self.assertEqual(len(
            response_follower.context["page_obj"]), self.TEST_AMOUNT_POSTS + 1)
        response_follower_other = self.follower_other.get(
            reverse('posts:follow_index',))
        self.assertEqual(len(response_follower_other.context["page_obj"]), 0)
