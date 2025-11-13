from django.contrib import admin
from .models import Player, Inventory, LeaderboardEntry

# Custom Admin for Player model to show important details
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'player_name', 
        'credits', 
        'current_era', 
        'best_time_seconds',
        'game_start_time'
    )
    search_fields = ('player_name',)
    list_filter = ('current_era',)

# Admin for Inventory (can be inline if needed, but simple list is fine)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'player', 
        'item_name', 
        'quantity', 
        'purchase_era_index'
    )
    list_filter = ('item_name',)
    search_fields = ('player__player_name', 'item_name')

# Admin for Leaderboard (ordered by time)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = (
        'player_name', 
        'time_seconds', 
        'date_recorded' # CORRECTED: This now matches models.LeaderboardEntry.date_recorded
    )
    list_filter = ('player_name',)
    ordering = ('time_seconds',)

# Register all models with their respective admin classes
admin.site.register(Player, PlayerAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(LeaderboardEntry, LeaderboardEntryAdmin)