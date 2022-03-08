from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_PER_PAGE = 10


def index(request):
    template = 'posts/index.html'
    title = 'Это главная страница проекта Yatube'
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    title = group.title
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_count = author.posts.count()
    template = 'posts/profile.html'
    full_name = author.get_full_name()
    title = 'Профайл пользователя ' + full_name
    following = False
    if ((request.user.is_authenticated)
        and Follow.objects.filter(
            user=request.user, author=author).exists()):
        following = True
    context = {
        'title': title,
        'page_obj': page_obj,
        'post_count': post_count,
        'full_name': full_name,
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_date = post.pub_date
    post_author = post.author.get_full_name
    post_count = post.author.posts.count()
    template = 'posts/post_detail.html'
    form = CommentForm(request.POST or None)
    comments = post.comment.all()
    context = {
        'post': post,
        'title': post.text[:30],
        'post_author': post_author,
        'post_count': post_count,
        'post_date': post_date,
        'form': form,
        'comments': comments
    }
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Последние обновления в ваших подписках'
    authors = Follow.objects.filter(
        user=request.user).values_list('author_id', flat=True)
    post_list = Post.objects.filter(
        author_id__in=authors).order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if request.user != get_object_or_404(User, username=username):
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
        return redirect('posts:profile', username=username)
    else:
        return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author_f = get_object_or_404(User, username=username)
    old_follow = Follow.objects.filter(
        user=request.user, author=author_f)
    old_follow.delete()
    return redirect('posts:profile', username=username)
