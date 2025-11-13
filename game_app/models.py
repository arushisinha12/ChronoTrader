from django.db import models
# JSONField is standard in recent Django versions (3.1+).
# If using older Django/Postgres, ensure necessary imports/settings.

class Player(models.Model):
    """Stores the persistent data for a single Temporal Trader profile."""
    player_name = models.CharField(max_length=100, unique=True, verbose_name="Trader Identifier", default="ChronoTrader")
    credits = models.IntegerField(default=100)
    current_era_index = models.IntegerField(default=0)
    current_era = models.CharField(max_length=50, default='Stone Age')
    
    # Game Time Tracking
    game_start_time = models.DateTimeField(null=True, blank=True)
    best_time_seconds = models.IntegerField(default=0, verbose_name="Personal Best Time (s)")
    
    # Store dynamic market prices for the current era
    current_prices = models.JSONField(default=dict)

    def __str__(self):
        return f"Trader: {self.player_name} ({self.credits} credits)"

class Inventory(models.Model):
    """Stores items possessed by a Player."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='inventory')
    item_name = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    purchase_era_index = models.IntegerField(default=-1) 

    class Meta:
        # Ensures a player can only hold one entry per item type
        unique_together = ('player', 'item_name')
        verbose_name_plural = "Inventories"

    def __str__(self):
        return f"{self.player.player_name}: {self.quantity} x {self.item_name}"

class LeaderboardEntry(models.Model):
    """Records a single successful game completion time."""
    player_name = models.CharField(max_length=50, default='Anonymous Chrono-Trader')
    time_seconds = models.IntegerField()
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['time_seconds', 'date_recorded']
        verbose_name_plural = "Leaderboard Entries"

    def __str__(self):
        return f"{self.player_name}: {self.time_seconds}s"