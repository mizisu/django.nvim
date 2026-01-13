from functools import wraps

from django.db import models
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, Comment, Post, Tag
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    TagSerializer,
)


# =============================================================================
# Edge Case 3: Multiple decorators on @action
# Expected: Detection fails if @action is more than 3 lines above def
# =============================================================================
def log_action(func):
    """Action logging decorator"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def rate_limit(calls_per_minute=60):
    """Rate limiting decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_response(timeout=300):
    """Response caching decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_params(required_params=None):
    """Parameter validation decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Edge Case 4: Decorator without @wraps (drf-spectacular's extend_schema)
# Expected: Source location should point to the actual method, not the class
# =============================================================================
def api_docs_comment_stats():
    """Real @extend_schema decorator wrapped in function - simulates lemonbase pattern"""
    return extend_schema(
        tags=["comments"],
        operation_id="comment_stats",
        description="Get comment statistics",
    )


def api_docs_comment_detailed_info():
    """Another @extend_schema decorator wrapped in function"""
    return extend_schema(
        tags=["comments"],
        operation_id="comment_detailed_info",
        description="Get detailed comment information",
    )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def posts(self, request, slug=None):
        category = self.get_object()
        posts = category.posts.filter(status="published")
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        categories = self.queryset.annotate(posts_count=models.Count("posts")).order_by(
            "-posts_count"
        )[:5]
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def posts(self, request, slug=None):
        tag = self.get_object()
        posts = tag.posts.filter(status="published")
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            status_filter = self.request.query_params.get("status", "published")
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, slug=None):
        post = self.get_object()
        post.status = "published"
        post.published_at = timezone.now()
        post.save()
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def archive(self, request, slug=None):
        post = self.get_object()
        post.status = "archived"
        post.save()
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def increment_views(self, request, slug=None):
        post = self.get_object()
        post.views_count += 1
        post.save()
        return Response({"views_count": post.views_count})

    @action(detail=False, methods=["get"])
    def featured(self, request):
        posts = self.queryset.filter(is_featured=True, status="published")
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        posts = self.queryset.filter(status="published").order_by("-views_count")[:10]
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def comments(self, request, slug=None):
        post = self.get_object()
        comments = post.comments.filter(parent__isnull=True)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_author(self, request):
        author_id = request.query_params.get("author_id")
        if not author_id:
            return Response(
                {"error": "author_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        posts = self.queryset.filter(author_id=author_id, status="published")
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    # =========================================================================
    # url_path Examples - 커스텀 URL 경로 지정
    # =========================================================================

    # 1. 기본 url_path 사용 (detail=False) - 하이픈이 포함된 URL
    @action(detail=False, methods=["get"], url_path="latest-posts")
    def get_latest_posts(self, request):
        """url_path로 하이픈이 포함된 URL 생성: /posts/latest-posts/"""
        posts = self.queryset.filter(status="published").order_by("-published_at")[:5]
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    # 2. 중첩 경로 (detail=False) - 슬래시가 포함된 URL
    @action(detail=False, methods=["get"], url_path="stats/summary")
    def stats_summary(self, request):
        """중첩된 URL 경로: /posts/stats/summary/"""
        total = self.queryset.count()
        published = self.queryset.filter(status="published").count()
        return Response({"total": total, "published": published})

    # 3. url_path + url_name (detail=True)
    @action(detail=True, methods=["get"], url_path="related-posts", url_name="related")
    def get_related_posts(self, request, slug=None):
        """url_path와 url_name 함께 사용: /posts/{slug}/related-posts/
        reverse('post-related', args=[slug])로 URL 생성 가능"""
        post = self.get_object()
        related = self.queryset.filter(
            category=post.category, status="published"
        ).exclude(pk=post.pk)[:5]
        serializer = PostListSerializer(related, many=True)
        return Response(serializer.data)

    # 4. 동적 경로 파라미터 (detail=True) - regex 패턴
    @action(detail=True, methods=["get"], url_path=r"history/(?P<year>[0-9]{4})")
    def view_history_by_year(self, request, slug=None, year=None):
        """동적 URL 파라미터: /posts/{slug}/history/2024/"""
        post = self.get_object()
        return Response(
            {"post_id": post.id, "year": year, "message": f"Viewing history for {year}"}
        )

    # 5. 단순 url_path (detail=True) - 하이픈 URL
    @action(detail=True, methods=["get"], url_path="reading-time")
    def get_reading_time(self, request, slug=None):
        """detail=True와 url_path: /posts/{slug}/reading-time/"""
        post = self.get_object()
        word_count = len(post.content.split()) if post.content else 0
        reading_time = max(1, word_count // 200)  # 분당 200단어 기준
        return Response(
            {"reading_time_minutes": reading_time, "word_count": word_count}
        )


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.query_params.get("post_id")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.all()
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

    # =========================================================================
    # Edge Case 3-1: 2 decorators (2 lines above def) - detected
    # =========================================================================
    @action(detail=True, methods=["get"])
    @log_action
    def activity_log_2_decorators(self, request, pk=None):
        """2 decorators - @action is 2 lines above def (detected)"""
        comment = self.get_object()
        return Response({"comment_id": comment.id, "activity": "viewed"})

    # =========================================================================
    # Edge Case 3-2: 3 decorators (3 lines above def) - detected (boundary)
    # =========================================================================
    @action(detail=True, methods=["post"])
    @log_action
    @rate_limit(calls_per_minute=30)
    def report_3_decorators(self, request, pk=None):
        """3 decorators - @action is 3 lines above def (boundary, detected)"""
        comment = self.get_object()
        return Response({"comment_id": comment.id, "reported": True})

    # =========================================================================
    # Edge Case 3-3: 4 decorators (4 lines above def) - detection failure!
    # =========================================================================
    @action(detail=True, methods=["get"])
    @log_action
    @rate_limit(calls_per_minute=10)
    @cache_response(timeout=600)
    def detailed_stats_4_decorators(self, request, pk=None):
        """4 decorators - @action is 4 lines above def (detection failure!)"""
        comment = self.get_object()
        return Response(
            {
                "comment_id": comment.id,
                "likes": 0,
                "replies_count": comment.replies.count(),
            }
        )

    # =========================================================================
    # Edge Case 3-4: 5 decorators (5 lines above def) - detection failure!
    # =========================================================================
    @action(detail=False, methods=["get"])
    @log_action
    @rate_limit(calls_per_minute=5)
    @cache_response(timeout=3600)
    @validate_params(required_params=["post_id"])
    def analytics_5_decorators(self, request):
        """5 decorators - @action is 5 lines above def (detection failure!)"""
        post_id = request.query_params.get("post_id")
        comments = self.queryset.filter(post_id=post_id)
        return Response(
            {
                "post_id": post_id,
                "total_comments": comments.count(),
                "approved_comments": comments.filter(is_approved=True).count(),
            }
        )

    # =========================================================================
    # Edge Case 4-1: @extend_schema + @action + @authentication (lemonbase pattern)
    # =========================================================================
    @api_docs_comment_stats()
    @action(detail=True, methods=["get"])
    def stats_with_schema(self, request, pk=None):
        """@extend_schema on top, @action in middle, auth at bottom"""
        comment = self.get_object()
        return Response({"comment_id": comment.id})

    # =========================================================================
    # Edge Case 4-2: @extend_schema() + @action + multiple decorators
    # =========================================================================
    @api_docs_comment_detailed_info()
    @action(detail=True, methods=["get"], url_path="detailed-info")
    @log_action
    def detailed_info(self, request, pk=None):
        """@extend_schema on top, @action, then @log_action and @authentication"""
        comment = self.get_object()
        return Response({"comment_id": comment.id, "content": comment.content})
