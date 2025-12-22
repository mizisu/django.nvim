from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = "shop"

# Main router for top-level resources
router = DefaultRouter()
router.register(r"products", viewsets.ProductViewSet, basename="product")
router.register(r"reviews", viewsets.ProductReviewViewSet, basename="review")
router.register(
    r"product-images", viewsets.ProductImageViewSet, basename="product-image"
)
router.register(r"orders", viewsets.OrderViewSet, basename="order")

urlpatterns = [
    # DRF ViewSets with router
    path("api/v1/", include(router.urls)),
    # Custom nested routes for products
    path(
        "api/v1/products/<int:product_id>/reviews/",
        viewsets.ProductReviewViewSet.as_view({"get": "list", "post": "create"}),
        name="product-reviews-list",
    ),
    path(
        "api/v1/products/<int:product_id>/images/",
        viewsets.ProductImageViewSet.as_view({"get": "list", "post": "create"}),
        name="product-images-list",
    ),
]
