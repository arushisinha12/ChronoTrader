# game_app/urls.py

from django.urls import path
from . import views
app_name = 'game_app'
urlpatterns = [
    # 1. THE MISSING LINK: The main game page must be named 'game_console'
    path('', views.start_game, name='start_game'), 
    path('console/', views.game_console, name='game_console'),
    # 2. Existing URL patterns
    path('trade/', views.trade_item, name='trade_item'),
    path('jump/forward/', views.time_jump_forward, name='time_jump_forward'),
    path('jump/backward/', views.time_jump_backward, name='time_jump_backward'),
    path('reset/', views.reset_game, name='reset_game'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard_view'),
    path('game_over/', views.game_over, name='game_over'),
    path('game_over/clean/', views.game_over_clean, name='game_over_clean'),
    path('game_over/render/', views.game_over_render, name='game_over_render'),
]