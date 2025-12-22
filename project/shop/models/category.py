from django.db import models


class Category(models.TextChoices):
    ELECTRONICS = "electronics", "Electronics"
    CLOTHING = "clothing", "Clothing"
    BOOKS = "books", "Books"
    FOOD = "food", "Food"
    HOME = "home", "Home & Garden"
