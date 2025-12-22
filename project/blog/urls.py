from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import viewsets

app_name = "blog"

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"categories", viewsets.CategoryViewSet, basename="category")
router.register(r"tags", viewsets.TagViewSet, basename="tag")
router.register(r"blog-posts", viewsets.PostViewSet, basename="blog-post")
router.register(r"comments", viewsets.CommentViewSet, basename="comment")

urlpatterns = [
    # Function-based views
    path("", views.post_list, name="post_list"),
    path("post/<slug:slug>/", views.post_detail, name="post_detail"),
    path(
        "category/<slug:category_slug>/",
        views.post_by_category,
        name="post_by_category",
    ),
    # Class-based views
    path("posts/", views.PostListView.as_view(), name="posts_list_class"),
    path(
        "posts/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail_class"
    ),
    path("featured/", views.FeaturedPostsView.as_view(), name="featured_posts"),
    path("search/", views.SearchView.as_view(), name="search"),
    # Archive views
    path("archive/<int:year>/", views.ArchiveView.as_view(), name="archive_year"),
    path(
        "archive/<int:year>/<int:month>/",
        views.ArchiveView.as_view(),
        name="archive_month",
    ),
    # API endpoints - function-based
    path("api/posts/", views.api_post_list, name="api_post_list"),
    path("api/posts/<int:pk>/", views.api_post_detail, name="api_post_detail"),
    # API endpoints - class-based (APIView)
    path("api/categories/", views.CategoryAPIView.as_view(), name="api_category_list"),
    path(
        "api/categories/<int:pk>/",
        views.CategoryDetailAPIView.as_view(),
        name="api_category_detail",
    ),
    path(
        "api/posts/<int:post_id>/comments/",
        views.CommentAPIView.as_view(),
        name="api_post_comments",
    ),
    # API endpoints - ViewSets with router
    path("api/v1/", include(router.urls)),
]
