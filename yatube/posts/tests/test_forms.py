import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_user')
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
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            text='test_comment',
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_create_post(self):
        """Валидная форма post_create создает post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст новго поста',
            'group': self.group.id,
            'image': self.post.image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст новго поста'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма post_edit меняет post."""
        post_count = Post.objects.count()
        form_data = {'text': 'Новый текст'}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст'
            ).exists()
        )

    def test_guest_user_cannot_edit_post(self):
        """Гость не может изменить пост."""
        post_count = Post.objects.count()
        form_data = {'text': 'Новый текст'}
        response_guest = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response_guest, f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertFalse(Post.objects.filter(text='Новый текст').exists())
        self.assertEqual(Post.objects.count(), post_count)

    def test_guest_user_cannot_add_comment(self):
        """Гость не может добавить комментарий."""
        comment_count = Comment.objects.count()
        form_data = {'comment': 'new comment'}
        response_guest = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response_guest, f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_create_comment(self):
        """Валидная форма comment создает comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'new comment of authorized user',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='new comment of authorized user'
            ).exists()
        )
