from rest_framework import serializers
from .models import Category, Tag, Post, Comment, PostView


class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "created_at", "posts_count"]
        read_only_fields = ["created_at"]

    def get_posts_count(self, obj):
        return obj.posts.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "author_name",
            "category_name",
            "tags",
            "excerpt",
            "status",
            "featured_image",
            "views_count",
            "is_featured",
            "published_at",
            "created_at",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class PostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "author_name",
            "category",
            "tags",
            "content",
            "excerpt",
            "status",
            "featured_image",
            "views_count",
            "is_featured",
            "published_at",
            "created_at",
            "updated_at",
            "comments_count",
        ]
        read_only_fields = ["author", "views_count", "created_at", "updated_at"]

    def get_comments_count(self, obj):
        return obj.comments.count()


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "category",
            "tags",
            "content",
            "excerpt",
            "status",
            "featured_image",
            "is_featured",
            "published_at",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "author_name",
            "parent",
            "content",
            "is_approved",
            "created_at",
            "updated_at",
            "replies",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


class PostViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostView
        fields = ["id", "post", "user", "ip_address", "viewed_at"]
        read_only_fields = ["viewed_at"]
