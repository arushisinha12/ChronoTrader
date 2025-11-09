# game_app/models.py

from django.db import models
from django.contrib.auth.models import User
# NOTE: If using Django < 3.1, you may need to use: 
# from django.contrib.postgres.fields import JSONField 

class Player(models.Model):
    # Default fields
    credits = models.IntegerField(default=100)
    current_era = models.CharField(max_length=50, default='Ancient Rome')
    current_era_index = models.IntegerField(default=0)
    # 🆕 NEW: Field to store the current, stable, fluctuating prices for the era
    current_prices = models.JSONField(default=dict) 

    def __str__(self):
        return f"Time Trader Player ({self.current_era})"
    
    game_start_time = models.DateTimeField(null=True, blank=True)
    best_time_seconds = models.IntegerField(default=0) # To store final score

class Inventory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    
    # 🚨 CRITICAL ADDITION: Tracks the era index where the item was purchased.
    purchase_era_index = models.IntegerField(default=-1) 

    class Meta:
        unique_together = ('player', 'item_name')

    def __str__(self):
        return f"{self.item_name} x{self.quantity} (Bought in Era {self.purchase_era_index})"
      
# game_app/models.py
class LeaderboardEntry(models.Model):
    # If using Django's built-in User model:
    # player_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Or, if using session-based tracking/username prompt:
    player_name = models.CharField(max_length=50, default='Anonymous Chrono-Trader')
    
    time_seconds = models.IntegerField()
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Crucial: Order by shortest time first
        ordering = ['time_seconds', 'date_recorded'] 

    def __str__(self):
        return f"{self.player_name}: {self.time_seconds}s"

