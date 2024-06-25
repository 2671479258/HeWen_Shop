
from django.urls import path
from goods import views

urlpatterns = [
path('list/<category_id>/skus/', views.ListView.as_view()),


]

