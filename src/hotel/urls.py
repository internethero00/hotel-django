from django.urls import path

from hotel import views

urlpatterns = [
    path("rooms/create", views.RoomCreateView.as_view(), name="room-create"),
    path("rooms/list", views.RoomListView.as_view(), name="room-list"),
    path("rooms/<int:pk>/delete", views.RoomDeleteView.as_view(), name="room-delete"),
    path("bookings/create", views.BookingCreateView.as_view(), name="booking-create"),
    path("bookings/<int:pk>/delete", views.BookingDeleteView.as_view(), name="booking-delete"),
    path("bookings/list", views.BookingListView.as_view(), name="booking-list"),
]
