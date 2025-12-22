from rest_framework import serializers
from .models import Product, ProductReview, ProductImage, Order, OrderItem


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "order", "created_at"]
        read_only_fields = ["created_at"]


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",
            "user",
            "user_name",
            "rating",
            "title",
            "comment",
            "is_verified_purchase",
            "helpful_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "helpful_count", "created_at", "updated_at"]


class ProductListSerializer(serializers.ModelSerializer):
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "price",
            "discount_price",
            "stock",
            "is_available",
            "is_featured",
            "rating",
            "image",
            "reviews_count",
            "average_rating",
            "created_at",
        ]

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return sum(r.rating for r in reviews) / reviews.count()
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "price",
            "discount_price",
            "stock",
            "is_available",
            "is_featured",
            "rating",
            "image",
            "images",
            "reviews",
            "reviews_count",
            "average_rating",
            "created_at",
            "updated_at",
        ]

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return sum(r.rating for r in reviews) / reviews.count()
        return None


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "price",
            "discount_price",
            "stock",
            "is_available",
            "is_featured",
            "image",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_price",
            "quantity",
            "subtotal",
            "created_at",
        ]
        read_only_fields = ["product_name", "product_price", "subtotal", "created_at"]


class OrderListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "user_name",
            "order_number",
            "status",
            "payment_method",
            "total",
            "is_paid",
            "items_count",
            "created_at",
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "user_name",
            "order_number",
            "status",
            "payment_method",
            "subtotal",
            "tax",
            "shipping_cost",
            "total",
            "shipping_address",
            "billing_address",
            "customer_notes",
            "is_paid",
            "paid_at",
            "shipped_at",
            "delivered_at",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "order_number",
            "is_paid",
            "paid_at",
            "shipped_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "payment_method",
            "shipping_address",
            "billing_address",
            "customer_notes",
            "items",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order
