from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api),
    path('search/', views.search_games),

    path('register/', views.register),
    path('login/', views.login_view),
    path('history/', views.get_search_history),

    path('game/<int:game_id>/', views.game_detail),
    path('game/<int:game_id>/achievements/', views.get_achievements),
    path('game/<int:game_id>/price/', views.get_price),
    path('game/<int:game_id>/price-history/', views.get_price_history),
]