import random
from datetime import datetime, timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
# Required import for database aggregation functions
from django.db import models 
from .models import Player, Inventory, LeaderboardEntry
# Assuming you have the following in constants.py:
from .constants import ERA_ORDER, ERAS, FUEL_GOAL, generate_era_prices

# The cost of time travel remains
TIME_JUMP_COST = 50

# --- UTILITY FUNCTIONS ---
def format_time(seconds):
    """Converts total seconds into M:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}m {secs:02d}s"

def get_current_player(request):
    """Utility to retrieve the player object based on session, or return None."""
    player_id = request.session.get('player_id')
    if not player_id:
        return None
    try:
        return Player.objects.get(pk=player_id)
    except Player.DoesNotExist:
        # Clear stale session data
        if 'player_id' in request.session:
            del request.session['player_id']
        return None

# ------------------------------------------------
# ## CORE VIEWS ##
# ------------------------------------------------

def start_game(request):
    """Handles player name entry and session creation/lookup."""
    player = get_current_player(request)
    
    if player:
        # Player is identified via session, continue to game
        return redirect('game_app:game_console')

    if request.method == 'POST':
        player_name = request.POST.get('player_name', '').strip()
        if not player_name:
            messages.error(request, "Please enter a valid player name.")
            return render(request, 'game_app/start_screen.html') 

        # Check if a player with this name already exists 
        try:
            player = Player.objects.get(player_name=player_name)
            messages.info(request, f"Welcome back, {player_name}! Loading previous state.")
        except Player.DoesNotExist:
            # If new name, create a brand new player
            player = Player.objects.create(player_name=player_name)
            messages.success(request, f"New Temporal Trader profile created for {player_name}.")

        # Store the player's ID in the session for persistence on this device
        request.session['player_id'] = player.pk
        
        # Initialize the game state (a hard reset for the identified player)
        return redirect('game_app:reset_game') 
            
    # Show the name entry form
    return render(request, 'game_app/start_screen.html')


def game_console(request):
    player = get_current_player(request)
    if not player:
        return redirect('game_app:start_game')
        
    current_era_index = player.current_era_index
    current_era_name = ERA_ORDER[current_era_index]
    static_era_data = ERAS[current_era_name]
    
    # 1. PRICE FLUCTUATION CHECK
    fluctuating_prices_data = player.current_prices
    
    if not fluctuating_prices_data or not fluctuating_prices_data.get('buy_prices'):
        fluctuating_prices_data = generate_era_prices(current_era_name)
        player.current_prices = fluctuating_prices_data
        player.save()
        
    # 2. CONSTRUCT ERA DATA for TEMPLATE
    era_data_for_template = {
        'currency': static_era_data['currency'],
        'trade_items': fluctuating_prices_data.get('buy_prices', {}),
        'sell_prices': fluctuating_prices_data.get('sell_prices', {}),
    }

    # 3. PREPARE INVENTORY FOR DISPLAY AND CHECK LOSS CONDITION
    inventory = []
    fuel_count = 0
    player_inventory = Inventory.objects.filter(player=player, quantity__gt=0)
    
    # Calculate potential cash from selling ALL inventory items at current market prices
    potential_sell_value = 0
    sell_prices = fluctuating_prices_data.get('sell_prices', {})
    
    for inv_item in player_inventory:
        if inv_item.item_name.lower() == 'gold coin':
            fuel_count += inv_item.quantity
            
        item_sell_price = sell_prices.get(inv_item.item_name)
        if item_sell_price is not None:
            potential_sell_value += inv_item.quantity * item_sell_price
            
        item_data = {
            'item_name': inv_item.item_name,
            'quantity': inv_item.quantity,
            'purchase_era_index': inv_item.purchase_era_index, 
            'sell_price': item_sell_price,
        }
        inventory.append(item_data)

    # --- LOSS CONDITION CHECK ---
    total_potential_credits = player.credits + potential_sell_value
    
    if total_potential_credits < TIME_JUMP_COST and fuel_count < FUEL_GOAL:
        messages.error(request, "GAME OVER! You have been stranded in time. Your current credits and total potential inventory value are below the cost of a temporal jump.")
        return redirect('game_app:game_over')
    # --------------------------
        
    # 4. HANDLE WIN CONDITION
    win_status = False
    final_time = None
    
    if fuel_count >= FUEL_GOAL:
        win_status = True
        
        if player.game_start_time:
            time_elapsed_seconds = int((datetime.now(timezone.utc) - player.game_start_time).total_seconds())
            final_time = format_time(time_elapsed_seconds)
            
            # 1. Record this completed run to the central Leaderboard
            LeaderboardEntry.objects.create(
                player_name=player.player_name, 
                time_seconds=time_elapsed_seconds
            )

            # 2. Check and update personal best for the player object
            is_new_best = player.best_time_seconds == 0 or time_elapsed_seconds < player.best_time_seconds
            
            if is_new_best:
                player.best_time_seconds = time_elapsed_seconds
                messages.success(request, f"SUCCESS! Protocol completed in {final_time}. NEW RECORD TIME! Your time has been recorded to the global leaderboard.")
            else:
                 messages.success(request, f"SUCCESS! Protocol completed in {final_time}. Your time has been recorded.")
            
            # Reset game start time so refreshing doesn't keep generating leaderboard entries
            player.game_start_time = None 
            player.save()
        
    # ------------------------------------------------------------------
    # ✅ FIXED: MOVE THE best_time_friendly CALCULATION TO THE END
    # Ensures it uses the current player.best_time_seconds value (saved above if won)
    # ------------------------------------------------------------------
    best_time_friendly = format_time(player.best_time_seconds) if player.best_time_seconds > 0 else "N/A"
    
    # 5. CONTEXT AND RENDER
    context = {
        'player': player,
        'era_name': current_era_name,
        'era_data': era_data_for_template,
        'inventory': inventory,
        'fuel_count': fuel_count,
        'FUEL_GOAL': FUEL_GOAL,
        'TIME_JUMP_COST': TIME_JUMP_COST, # Added for completeness
        'current_era_index': current_era_index, 
        'game_start_timestamp': player.game_start_time.timestamp() * 1000 if player.game_start_time else None,
        'best_time_friendly': best_time_friendly,
        
        # Win screen context (for modal)
        'win_status': win_status,
        'final_time': final_time,
    }
    
    return render(request, 'game_app/game_template.html', context) 


@transaction.atomic
def trade_item(request):
    if request.method != 'POST':
        return redirect('game_app:game_console')

    player = get_current_player(request)
    if not player:
        messages.error(request, "Session expired. Please start a new game.")
        return redirect('game_app:start_game')
        
    item_name = request.POST.get('item_name')
    action = request.POST.get('action')
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        messages.error(request, "Invalid quantity specified.")
        return redirect('game_app:game_console')

    current_prices = player.current_prices
    current_era_name = ERA_ORDER[player.current_era_index]
    current_currency = ERAS[current_era_name]['currency']

    # --- BUY LOGIC ---
    if action == 'buy':
        buy_prices = current_prices.get('buy_prices', {})
        price = buy_prices.get(item_name)
        
        if price is None:
            messages.error(request, f"Item '{item_name}' is not available for purchase in {current_era_name}.")
            return redirect('game_app:game_console')
        
        cost = price * quantity

        if player.credits < cost:
            messages.error(request, f"Insufficient credits! Need {cost} {current_currency}.")
            return redirect('game_app:game_console')

        # Execute Transaction
        player.credits -= cost
        player.save()
        
        item, created = Inventory.objects.get_or_create(
            player=player,
            item_name=item_name,
            defaults={'purchase_era_index': player.current_era_index, 'quantity': 0}
        )
        
        item.quantity += quantity
        item.purchase_era_index = player.current_era_index 
        item.save()

        messages.success(request, f"Acquired {quantity} x {item_name} for {cost} {current_currency}.")

    # --- SELL LOGIC ---
    elif action == 'sell':
        sell_prices = current_prices.get('sell_prices', {})
        sell_price = sell_prices.get(item_name)
        
        try:
            item = Inventory.objects.get(player=player, item_name=item_name)
        except Inventory.DoesNotExist:
            messages.error(request, f"You do not possess {item_name}.")
            return redirect('game_app:game_console')

        if sell_price is None:
            messages.warning(request, f"No market demand (sell price) for {item_name} in this era.")
            return redirect('game_app:game_console')

        if item.quantity < quantity:
            messages.error(request, f"Insufficient quantity of {item_name} to sell. You only have {item.quantity}.")
            return redirect('game_app:game_console')
        
        # Execute Transaction
        revenue = sell_price * quantity
        player.credits += revenue
        player.save()

        item.quantity -= quantity
        
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

        messages.success(request, f"Liquidated {quantity} x {item_name} for {revenue} credits.")
        
    # After a trade, redirect back to the console which will re-run the loss check
    return redirect('game_app:game_console')

def time_jump_forward(request):
    return time_jump(request, 'forward')

def time_jump_backward(request):
    return time_jump(request, 'backward')


@transaction.atomic
def time_jump(request, direction):
    global TIME_JUMP_COST 
    
    player = get_current_player(request)
    if not player:
        messages.error(request, "Session expired. Please start a new game.")
        return redirect('game_app:start_game')

    # CHECK AND DEDUCT COST
    if player.credits < TIME_JUMP_COST:
        # NOTE: This check is also done in game_console, but it's crucial here too
        messages.error(request, f"INSUFFICIENT FUNDS. Cannot afford the temporal traversal fee of {TIME_JUMP_COST} credits.")
        return redirect('game_app:game_console')
    
    player.credits -= TIME_JUMP_COST 

    current_index = player.current_era_index
    num_eras = len(ERA_ORDER)

    if direction == 'forward':
        next_index = (current_index + 1) % num_eras
        jump_message = "advanced to"
    elif direction == 'backward':
        next_index = (current_index - 1 + num_eras) % num_eras
        jump_message = "retreated to"
    else:
        messages.error(request, "Invalid jump direction.")
        return redirect('game_app:game_console')

    # Update Player State
    player.current_era_index = next_index
    player.current_era = ERA_ORDER[next_index]
    
    # GENERATE AND SAVE NEW FLUCTUATING PRICES
    new_era_name = ERA_ORDER[next_index]
    new_prices_data = generate_era_prices(new_era_name)
    player.current_prices = new_prices_data
    
    player.save() 
    messages.info(request, f"Successfully {jump_message} the {player.current_era}. Traversal fee of {TIME_JUMP_COST} credits deducted. Market conditions have shifted.")
    return redirect('game_app:game_console')


@transaction.atomic
def reset_game(request):
    player = get_current_player(request)
    if not player:
        return redirect('game_app:start_game')
        
    # --- 1. Define Initial Starting Inventory ---
    initial_items_data = [
        ('candy bar', 5), 
        ('rubber duck', 2),
    ]
        
    # --- 2. Reset Player fields for the identified player ---
    player.credits = 100
    player.current_era_index = 0
    player.current_era = ERA_ORDER[0]
    player.game_start_time = datetime.now(timezone.utc)
    # player.best_time_seconds persists
    # player.best_time_seconds = 0 

    # Generate initial prices for the starting era
    player.current_prices = generate_era_prices(player.current_era)
    
    # Save Player and clear existing Inventory (only for THIS player)
    player.save()
    Inventory.objects.filter(player=player).delete()
    
    # --- 3. ADD INITIAL INVENTORY ITEMS ---
    starting_era_index = player.current_era_index
    
    for item_name, quantity in initial_items_data:
        Inventory.objects.create(
            player=player,
            item_name=item_name,
            quantity=quantity,
            purchase_era_index=starting_era_index 
        )

    game_instructions = (
        f"Welcome, {player.player_name}! Your new protocol is active. "
        "Your ultimate objective is to acquire 5 Gold Coins (Fuel). "
        "Use the Jump buttons to travel the timeline and exploit market shifts. "
        "Remember: Items purchased locally are sold at a steep loss in the same era. You must travel to profit!"
    )
    messages.info(request, game_instructions)
    
    messages.success(request, f"New Protocol initiated for {player.player_name}. Welcome to the start of the timeline.")
    return redirect('game_app:game_console')


# --- LEADERBOARD (SHOWS ONLY BEST TIME PER PLAYER) ---

def leaderboard_view(request):
    # 1. Group records by player_name and find the minimum (best) time
    best_scores_queryset = LeaderboardEntry.objects.values('player_name').annotate(
        best_time_seconds=models.Min('time_seconds')
    # 2. Order by the best time (fastest first)
    ).order_by('best_time_seconds')[:10]
    
    # 3. Process and format the results for the template
    formatted_entries = []
    for rank, entry in enumerate(best_scores_queryset, 1):
        formatted_entries.append({
            'rank': rank,
            'player_name': entry['player_name'],
            'time': format_time(entry['best_time_seconds']),
            'time_seconds': entry['best_time_seconds'],
        })

    context = {
        'leaderboard_entries': formatted_entries
    }
    return render(request, 'game_app/leaderboard.html', context)


# --- NEW GAME OVER VIEW (FIXED FORMAT_TIME ISSUE) ---

def game_over(request):
    """Renders the game over screen when player can no longer afford a time jump."""
    player = get_current_player(request)
    if not player:
        return redirect('game_app:start_game')
    
    # Reset game start time to mark the session as concluded
    if player.game_start_time:
        player.game_start_time = None 
        player.save()
    
    # FIX: Calculate the friendly time string here before passing to context
    best_time_friendly = format_time(player.best_time_seconds) if player.best_time_seconds > 0 else "N/A"
        
    context = {
        'player': player,
        'TIME_JUMP_COST': TIME_JUMP_COST,
        'best_time_friendly': best_time_friendly, # Passing the pre-formatted string
    }
    return render(request, 'game_app/lose_screen.html', context)