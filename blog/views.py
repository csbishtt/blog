from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Post, Category, Comment, Like, Follow
from .forms import PostForm, CommentForm


# ---------------- HOME ----------------
def home(request):
    if request.user.is_authenticated:
        following_users = Follow.objects.filter(
            follower=request.user
        ).values_list('following', flat=True)

        posts = Post.objects.filter(
            Q(author__in=following_users) | Q(author=request.user),
            status='published'
        ).order_by('-created_at')
    else:
        posts = Post.objects.filter(
            status='published'
        ).order_by('-created_at')

    # SEARCH
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

    # PAGINATION
    paginator = Paginator(posts, 5)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    # TRENDING POSTS
    trending_posts = Post.objects.filter(
        status='published'
    ).order_by('-views')[:5]

    return render(request, 'home.html', {
        'posts': posts,
        'trending_posts': trending_posts
    })


# ---------------- POST DETAIL ----------------
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)

    post.views += 1
    post.save()

    comments = Comment.objects.filter(
        post=post
    ).order_by('-id')

    form = CommentForm()

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post_detail', slug=slug)

    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(
            user=request.user,
            post=post
        ).exists()

    like_count = Like.objects.filter(post=post).count()

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'liked': liked,
        'like_count': like_count
    })


# ---------------- CREATE POST ----------------
@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.status = "published"
        post.save()
        return redirect('home')

    return render(request, 'create_post.html', {'form': form})


# ---------------- EDIT POST ----------------
@login_required
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)

    if request.user != post.author:
        return redirect('home')

    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('post_detail', slug=post.slug)

    return render(request, 'create_post.html', {'form': form})


# ---------------- DELETE POST ----------------
@login_required
def delete_post(request, id):
    post = get_object_or_404(Post, id=id)

    if request.user != post.author:
        return redirect('home')

    post.delete()
    return redirect('home')


# ---------------- LIKE / UNLIKE ----------------
@login_required
def like_post(request, id):
    post = get_object_or_404(Post, id=id)

    liked_obj = Like.objects.filter(
        user=request.user,
        post=post
    )

    if liked_obj.exists():
        liked_obj.delete()
        liked = False
    else:
        Like.objects.create(
            user=request.user,
            post=post
        )
        liked = True

    like_count = Like.objects.filter(post=post).count()

    return JsonResponse({
        'liked': liked,
        'like_count': like_count
    })


# ---------------- DELETE COMMENT ----------------
@login_required
def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id)

    if request.user == comment.user or request.user == comment.post.author:
        comment.delete()

    return redirect('post_detail', slug=comment.post.slug)


# ---------------- DASHBOARD ----------------
@login_required
def dashboard(request):
    user = request.user
    posts = Post.objects.filter(author=user)

    total_posts = posts.count()
    total_views = posts.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = Like.objects.filter(
        post__author=user
    ).count()

    return render(request, 'dashboard.html', {
        'posts': posts,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_likes': total_likes
    })


# ---------------- REGISTER ----------------
def register(request):
    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')

    return render(request, 'register.html', {'form': form})


# ---------------- LOGIN ----------------
def user_login(request):
    error = ""

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            return redirect('home')
        else:
            error = "Invalid username or password"

    return render(request, 'login.html', {'error': error})


# ---------------- LOGOUT ----------------
def user_logout(request):
    logout(request)
    return redirect('home')


# ---------------- CATEGORY POSTS ----------------
def category_posts(request, id):
    category = get_object_or_404(Category, id=id)

    posts = Post.objects.filter(
        category=category,
        status='published'
    )

    return render(request, 'category.html', {
        'category': category,
        'posts': posts
    })


# ---------------- FOLLOW / UNFOLLOW ----------------
@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(
        User,
        username=username
    )

    obj = Follow.objects.filter(
        follower=request.user,
        following=user_to_follow
    )

    if obj.exists():
        obj.delete()
    else:
        Follow.objects.create(
            follower=request.user,
            following=user_to_follow
        )

    return redirect('profile', username=username)