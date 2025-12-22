from django.db import models
from django.utils import timezone
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
