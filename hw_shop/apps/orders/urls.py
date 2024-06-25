from django.urls import path
from . import views

urlpatterns = [
    path('orders/settlement/', views.OrderSettlementView.as_view()),
    path('orders/commit/', views.OrderCommitView.as_view()),

]