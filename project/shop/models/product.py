from django.contrib.auth.models import User
from django.db import models

from project.shop.models.category import Category


class Product(models.Model):
    class Availability(models.IntegerChoices):
        OUT_OF_STOCK = 0, "Out of Stock"
        LOW_STOCK = 1, "Low Stock"
        IN_STOCK = 2, "In Stock"
        PREORDER = 3, "Pre-order"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=50, choices=Category.choices)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock = models.PositiveIntegerField(default=0)
    availability = models.IntegerField(
        choices=Availability.choices, default=Availability.IN_STOCK
    )
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category", "-created_at"]),
        ]

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    class Rating(models.IntegerChoices):
        ONE_STAR = 1, "★☆☆☆☆"
        TWO_STARS = 2, "★★☆☆☆"
        THREE_STARS = 3, "★★★☆☆"
        FOUR_STARS = 4, "★★★★☆"
        FIVE_STARS = 5, "★★★★★"

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="product_reviews"
    )
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    title = models.CharField(max_length=100)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["product", "user"]]

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"
