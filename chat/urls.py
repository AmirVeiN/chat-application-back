from django.urls import path
from .views import CreateOrJoinRoomView, GetContactsView

urlpatterns = [
    path("create-or-join-room/", CreateOrJoinRoomView.as_view(), name="create-or-join-room"),
    path('contacts/', GetContactsView.as_view(), name='get-contacts'),
]