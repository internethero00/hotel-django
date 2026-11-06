from rest_framework.filters import OrderingFilter


class StableOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if ordering:
            return [*ordering, "id"]
        return ordering
