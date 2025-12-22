from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Avg
from .models import Product, ProductReview, ProductImage, Order, OrderItem
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductReviewSerializer,
    ProductImageSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    @action(detail=False, methods=["get"])
    def featured(self, request):
        products = self.queryset.filter(is_featured=True, is_available=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def on_sale(self, request):
        products = self.queryset.filter(discount_price__isnull=False, is_available=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        threshold = int(request.query_params.get("threshold", 10))
        products = self.queryset.filter(stock__lte=threshold, is_available=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        products = self.queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        product = self.get_object()
        reviews = product.reviews.all()
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_review(self, request, slug=None):
        product = self.get_object()
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def update_stock(self, request, slug=None):
        product = self.get_object()
        quantity = request.data.get("quantity")
        if quantity is None:
            return Response(
                {"error": "quantity is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        product.stock += int(quantity)
        product.save()
        return Response({"stock": product.stock})

    @action(detail=False, methods=["get"])
    def by_category(self, request):
        category = request.query_params.get("category")
        if not category:
            return Response(
                {"error": "category parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        products = self.queryset.filter(category=category, is_available=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        serializer = self.get_serializer(review)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ["shipped", "delivered"]:
            return Response(
                {"error": "Cannot cancel shipped or delivered orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "cancelled"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_paid(self, request, pk=None):
        order = self.get_object()
        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = "processing"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_shipped(self, request, pk=None):
        order = self.get_object()
        if not order.is_paid:
            return Response(
                {"error": "Cannot ship unpaid orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "shipped"
        order.shipped_at = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_delivered(self, request, pk=None):
        order = self.get_object()
        if order.status != "shipped":
            return Response(
                {"error": "Only shipped orders can be marked as delivered"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "delivered"
        order.delivered_at = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_orders(self, request):
        orders = self.queryset.filter(user=request.user)
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        orders = self.queryset.filter(status="pending")
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def processing(self, request):
        orders = self.queryset.filter(status="processing")
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
