from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views, viewsets

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
    # =========================================================================
    # Edge Case 1: Custom HTTP method view
    # Expected: only get() is detected, trace() and connect() are NOT detected
    # =========================================================================
    path("api/debug/", views.DebugAPIView.as_view(), name="api_debug"),
    # =========================================================================
    # Edge Case 2: View wrapped with decorator without functools.wraps
    # Expected: bad_decorator view may show function name as 'wrapper'
    # =========================================================================
    path("stats/bad-decorator/", views.post_stats_bad_decorator, name="stats_bad"),
    path("stats/good-decorator/", views.post_stats_good_decorator, name="stats_good"),
    # =========================================================================
    # Edge Case 5: Complex regex patterns with re_path
    # Expected: Detected but pattern is displayed as raw regex (poor readability)
    # =========================================================================
    re_path(
        r"^articles/(?P<year>[0-9]{4})/$",
        views.post_list,
        name="articles_by_year",
    ),
    re_path(
        r"^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$",
        views.post_list,
        name="articles_by_month",
    ),
    re_path(
        r"^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$",
        views.post_list,
        name="articles_by_day",
    ),
    # More complex regex: slug + optional page number
    re_path(
        r"^tag/(?P<tag_slug>[-\w]+)(?:/page/(?P<page>\d+))?/$",
        views.post_list,
        name="posts_by_tag",
    ),
]

# =============================================================================
# Edge Case 4: Dynamically generated URL patterns
# Expected: Detected at script execution time if included in urlpatterns
# However, conditional (if statement) patterns may be missed depending on condition
# =============================================================================

# 4-1: URL patterns generated with loop (detected)
DYNAMIC_CATEGORIES = ["tech", "lifestyle", "news"]
for category in DYNAMIC_CATEGORIES:
    urlpatterns.append(
        path(
            f"dynamic/{category}/",
            views.post_list,
            name=f"dynamic_{category}",
        )
    )

# 4-2: Conditional URL pattern - only added in DEBUG mode (detection depends on condition)
import os

if os.environ.get("DJANGO_DEBUG_URLS", "false").lower() == "true":
    urlpatterns.append(
        path(
            "conditional-debug/",
            views.post_list,
            name="conditional_debug",
        )
    )
