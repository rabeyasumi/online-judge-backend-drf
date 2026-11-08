from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError

from .pagination import ProblemPagination

from .models import Element
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer
)


class ProblemListView(generics.ListAPIView):
    serializer_class = ProblemListSerializer
    permission_classes = [AllowAny]
    pagination_class = ProblemPagination

    filter_backends = [SearchFilter]
    search_fields = ['pname']

    def get_queryset(self):
        queryset = Element.objects.all()

        rating = self.request.query_params.get('rating')
        category = self.request.query_params.get('category')

        if rating:
            try:
                rating = int(rating)
            except ValueError:
                raise ValidationError({
                    'rating': 'Rating must be an integer.'
                })

            queryset = queryset.filter(rating=rating)

        if category:
            queryset = queryset.filter(category__iexact=category)

        return queryset.order_by('-id')

class ProblemDetailView(generics.RetrieveAPIView):
    queryset = Element.objects.all()
    serializer_class = ProblemDetailSerializer
    permission_classes = [AllowAny]