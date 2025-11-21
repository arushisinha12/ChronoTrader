from django.urls import path
from . import views
app_name = 'game_app'
urlpatterns = [
    # Main entry point
    path('', views.start_game, name='start_game'), 
    # Game console
    path('console/', views.game_console, name='game_console'),
    
    # Trading actions
    path('trade/', views.trade_item, name='trade_item'),
    
    # Time Jump actions
    path('jump/forward/', views.time_jump_forward, name='time_jump_forward'),
    path('jump/backward/', views.time_jump_backward, name='time_jump_backward'),
    
    # Game state actions
    path('reset/', views.reset_game, name='reset_game'),
    
    # Leaderboard
    path('leaderboard/', views.leaderboard_view, name='leaderboard'), # Renamed for clarity
    
    # Game Over screen (direct render)
    path('game_over/render/', views.game_over_render, name='game_over_render'),
]