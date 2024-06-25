from django.urls import path
from users import views

urlpatterns = [

    path('register/',views.RegisterView.as_view()),
path('login/',views.LoginView.as_view()),
    path('logout/',views.LogoutView.as_view()),
    path('myorder/',views.MyOrder.as_view()),
    path('addresses/create/', views.AddressCreateView.as_view()),
    path('addresses/', views.ShowAddress.as_view()),
    path('addresses/<address_id>/', views.UpdateAddressView.as_view()),
    path('confirm_delivery/', views.confirmDelivery.as_view(), name='confirm_delivery'),

]