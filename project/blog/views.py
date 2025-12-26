from functools import wraps

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView, ListView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Comment, Post


# =============================================================================
# Edge Case 1: Custom HTTP methods (TRACE, CONNECT)
# Expected: trace(), connect() methods are NOT detected (not in hardcoded list)
# =============================================================================
class DebugAPIView(APIView):
    """Debug API view - supports non-standard methods like TRACE, CONNECT"""

    def get(self, request):
        """GET method - detected"""
        return Response({"method": "GET", "debug": True})

    def trace(self, request):
        """TRACE method - NOT detected (not in hardcoded list)"""
        return Response({"method": "TRACE", "headers": dict(request.headers)})

    def connect(self, request):
        """CONNECT method - NOT detected"""
        return Response({"method": "CONNECT"})


# =============================================================================
# Edge Case 2: Decorator without functools.wraps
# Expected: Original function info is lost, detection may fail
# =============================================================================
def bad_decorator_without_wraps(func):
    """Bad decorator that doesn't use functools.wraps"""

    def wrapper(request, *args, **kwargs):
        # Logging logic etc.
        return func(request, *args, **kwargs)

    return wrapper  # No wraps(func) - __name__, __module__ etc. are lost


def good_decorator_with_wraps(func):
    """Good decorator that properly uses functools.wraps"""

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)

    return wrapper


@bad_decorator_without_wraps
def post_stats_bad_decorator(request):
    """View wrapped with bad decorator - detection may fail"""
    stats = {
        "total_posts": Post.objects.count(),
        "published_posts": Post.objects.filter(status="published").count(),
    }
    return JsonResponse(stats)


@good_decorator_with_wraps
def post_stats_good_decorator(request):
    """View wrapped with good decorator - detected correctly"""
    stats = {
        "total_posts": Post.objects.count(),
        "draft_posts": Post.objects.filter(status="draft").count(),
    }
    return JsonResponse(stats)


def post_list(request):
    posts = Post.objects.filter("")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status="published")
    return render(request, "blog/post_detail.html", {"post": post})


def post_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.filter(category=category, status="published")
    return render(
        request, "blog/post_list.html", {"posts": posts, "category": category}
    )


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(status="published")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.filter(status__exact="published")


class FeaturedPostsView(View):
    def get(self, request):
        featured_posts = Post.objects.filter(is_featured=True, status="published")
        return render(request, "blog/featured_posts.html", {"posts": featured_posts})

    def post(self, request):
        return JsonResponse({"message": "Featured posts updated"})


@api_view(["GET", "POST"])
def api_post_list(request):
    if request.method == "GET":
        posts = Post.objects.filter(status="published")
        data = [{"title": p.title, "slug": p.slug} for p in posts]
        return Response(data)
    elif request.method == "POST":
        return Response({"message": "Post created"}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def api_post_detail(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        data = {
            "title": post.title,
            "content": post.content,
            "author": post.author.username,
        }
        return Response(data)
    elif request.method == "PUT":
        return Response({"message": "Post updated"})
    elif request.method == "PATCH":
        return Response({"message": "Post partially updated"})
    elif request.method == "DELETE":
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryAPIView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        data = [{"name": c.name, "slug": c.slug} for c in categories]
        return Response(data)

    def post(self, request):
        return Response({"message": "Category created"}, status=status.HTTP_201_CREATED)


class CategoryDetailAPIView(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        data = {
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
        }
        return Response(data)

    def put(self, request, pk):
        return Response({"message": "Category updated"})

    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentAPIView(APIView):
    def get(self, request, post_id):
        comments = Comment.objects.filter(post_id=post_id)
        data = [{"content": c.content, "author": c.author.username} for c in comments]
        return Response(data)

    def post(self, request, post_id):
        return Response({"message": "Comment created"}, status=status.HTTP_201_CREATED)


class SearchView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        results = (
            Post.objects.filter(title__icontains=query, status="published")
            if query
            else []
        )
        return render(request, "blog/search.html", {"results": results, "query": query})


class ArchiveView(ListView):
    model = Post
    template_name = "blog/archive.html"
    context_object_name = "posts"

    def get(self, request, year, month=None):
        posts = Post.objects.filter(published_at__year=year, status="published")
        if month:
            posts = posts.filter(published_at__month=month)
        return render(request, self.template_name, {"posts": posts})

    def post(self, request, year, month=None):
        return JsonResponse({"message": "Archive post method"})
