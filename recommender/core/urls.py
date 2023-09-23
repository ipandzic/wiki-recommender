from django.urls import re_path

from . import views

urlpatterns = [
    re_path('get-recommended-links/', views.get_recommended_links_view, name='get-recommended-links'),
]
