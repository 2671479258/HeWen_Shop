
from django.urls import path
from . import views
urlpatterns = [
    path('areas/',views.AreaView.as_view()),
    path('areas/<id>/',views.SubAreaView.as_view()),
]
