from django.urls import path

from hotel import views

urlpatterns = [
    path("rooms/create", views.RoomCreateView.as_view()),
    path("rooms/list", views.RoomListView.as_view()),
]
