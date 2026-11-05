from django.urls import path

from hotel import views

urlpatterns = [
    path("rooms/", views.RoomListCreateView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", views.RoomDetailView.as_view(), name="room-detail"),
    path("bookings/", views.BookingListCreateView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", views.BookingDetailView.as_view(), name="booking-detail"),
]
