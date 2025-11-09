import random
from datetime import datetime, timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Player, Inventory, LeaderboardEntry
# Assuming you have the following in constants.py:
# ERA_ORDER, ERAS, FUEL_GOAL, generate_era_prices
from .constants import ERA_ORDER, ERAS, FUEL_GOAL, generate_era_prices

# --- UTILITY FUNCTION ---
def format_time(seconds):
    """Converts total seconds into M:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}m {secs:02d}s"

# --- CORE VIEWS ---

def game_console(request):
    # Placeholder: Get or create a default player (assuming ID 1 for simplicity)
    try:
        player = Player.objects.get(pk=1)
    except Player.DoesNotExist:
        # Initialize a new game state if player doesn't exist
        player = Player.objects.create(pk=1)
        
    current_era_index = player.current_era_index
    current_era_name = ERA_ORDER[current_era_index]
    static_era_data = ERAS[current_era_name]
    
    # 1. PRICE FLUCTUATION CHECK (Generate if prices are missing or empty)
    fluctuating_prices_data = player.current_prices
    
    if not fluctuating_prices_data or not fluctuating_prices_data.get('buy_prices'):
        fluctuating_prices_data = generate_era_prices(current_era_name)
        player.current_prices = fluctuating_prices_data
        player.save()
        
    # 2. CONSTRUCT ERA DATA for TEMPLATE
    era_data_for_template = {
        'currency': static_era_data['currency'],
        # Use the fluctuating prices for both buying and selling
        'trade_items': fluctuating_prices_data.get('buy_prices', {}),
        'sell_prices': fluctuating_prices_data.get('sell_prices', {}),
    }

    # 3. PREPARE INVENTORY FOR DISPLAY
    inventory = []
    fuel_count = 0
    player_inventory = Inventory.objects.filter(player=player, quantity__gt=0)
    
    for inv_item in player_inventory:
        if inv_item.item_name.lower() == 'gold coin':
            fuel_count += inv_item.quantity
            
        # FIX: Set can_sell_status to True unconditionally (Option A)
        can_sell_status = True
            
        item_data = {
            'item_name': inv_item.item_name,
            'quantity': inv_item.quantity,
            'purchase_era_index': inv_item.purchase_era_index, 
            'can_sell': can_sell_status,
            'sell_price': era_data_for_template['sell_prices'].get(inv_item.item_name),
        }
        inventory.append(item_data)
        
    # 4. HANDLE WIN CONDITION
    win_status = False
    final_time = None
    best_time_friendly = format_time(player.best_time_seconds) if player.best_time_seconds > 0 else "N/A"
    
    if fuel_count >= FUEL_GOAL:
        win_status = True
        
        # Calculate final time if it's the first time winning this session
        if player.game_start_time:
            time_elapsed_seconds = int((datetime.now(timezone.utc) - player.game_start_time).total_seconds())
            final_time = format_time(time_elapsed_seconds)
            
            # Check for and record best time
            if player.best_time_seconds == 0 or time_elapsed_seconds < player.best_time_seconds:
                player.best_time_seconds = time_elapsed_seconds
                
                # Create Leaderboard Entry
                LeaderboardEntry.objects.create(
                    player_name=f"Trader-{random.randint(100, 999)}", # Placeholder name
                    time_seconds=time_elapsed_seconds
                )
            
            # Reset game start time so refreshing doesn't keep generating leaderboard entries
            player.game_start_time = None 
            player.save()
            messages.success(request, f"SUCCESS! Protocol completed in {final_time}.")
        
    # 5. CONTEXT AND RENDER
    context = {
        'player': player,
        'era_name': current_era_name,
        'era_data': era_data_for_template,
        'inventory': inventory,
        'fuel_count': fuel_count,
        'FUEL_GOAL': FUEL_GOAL,
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

    # Placeholder: Get player
    try:
        player = Player.objects.get(pk=1)
    except Player.DoesNotExist:
        messages.error(request, "Player state not found.")
        return redirect('game_app:game_console')
        
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

    # --- BUY LOGIC (Sets purchase_era_index) ---
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
        
        # Get or create the inventory item
        item, created = Inventory.objects.get_or_create(
            player=player,
            item_name=item_name,
            # If created, initialize with the current era index
            defaults={'purchase_era_index': player.current_era_index, 'quantity': 0}
        )
        
        item.quantity += quantity
        
        # Set/update the purchase_era_index to the current era upon buying
        item.purchase_era_index = player.current_era_index 
        item.save()

        messages.success(request, f"Acquired {quantity} x {item_name} for {cost} {current_currency}.")

    # --- SELL LOGIC (Economic Disincentive Used - Time Lock Message Removed) ---
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

        # ... (quantity checks and execution) ...
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
        
    return redirect('game_app:game_console')

def time_jump_forward(request):
    return time_jump(request, 'forward')

def time_jump_backward(request):
    return time_jump(request, 'backward')


@transaction.atomic
def time_jump(request, direction):
    # Placeholder: Get player
    try:
        player = Player.objects.get(pk=1)
    except Player.DoesNotExist:
        messages.error(request, "Player state not found.")
        return redirect('game_app:game_console')

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
    
    # CRITICAL: GENERATE AND SAVE NEW FLUCTUATING PRICES
    new_era_name = ERA_ORDER[next_index]
    new_prices_data = generate_era_prices(new_era_name)
    player.current_prices = new_prices_data
    
    player.save()
    messages.info(request, f"Successfully {jump_message} the {player.current_era}. Market conditions have shifted.")
    return redirect('game_app:game_console')


@transaction.atomic
def reset_game(request):
    # Placeholder: Get player
    try:
        player = Player.objects.get(pk=1)
    except Player.DoesNotExist:
        player = Player.objects.create(pk=1)
        
    # --- 1. Define Initial Starting Inventory ---
    initial_items_data = [
        # Item Name, Quantity
        ('candy bar', 5), 
        ('rubber duck', 2),
    ]
        
    # --- 2. Reset Player fields ---
    player.credits = 100
    player.current_era_index = 0
    player.current_era = ERA_ORDER[0]
    player.game_start_time = datetime.now(timezone.utc)
    
    # Generate initial prices for the starting era
    player.current_prices = generate_era_prices(player.current_era)
    
    # Save Player and clear existing Inventory
    player.save()
    Inventory.objects.filter(player=player).delete()
    
    # --- 3. ADD INITIAL INVENTORY ITEMS ---
    starting_era_index = player.current_era_index
    
    for item_name, quantity in initial_items_data:
        # Create the starting items for the player
        Inventory.objects.create(
            player=player,
            item_name=item_name,
            quantity=quantity,
            # CRITICAL: Set the purchase era index to 0
            purchase_era_index=starting_era_index 
        )

    # 🚨 NEW INSTRUCTION MESSAGE FOR NEW GAME START
    game_instructions = (
        "Welcome, Temporal Trader! Your new protocol is active. "
        "Your ultimate objective is to acquire 5 Gold Coins (Fuel). "
        "Use the Jump buttons to travel the timeline and exploit market shifts. "
        "Remember: Items purchased locally are sold at a steep loss in the same era. You must travel to profit!"
    )
    messages.info(request, game_instructions)
    
    messages.success(request, "New Protocol initiated. Credits restored and inventory purged. Basic supplies acquired. Welcome to the start of the timeline.")
    return redirect('game_app:game_console')


# --- LEADERBOARD ---

def leaderboard_view(request):
    # Fetch the top 10 scores
    leaderboard_entries = LeaderboardEntry.objects.all()[:10]
    
    formatted_entries = []
    for rank, entry in enumerate(leaderboard_entries, 1):
        formatted_entries.append({
            'rank': rank,
            'player_name': entry.player_name,
            'time': format_time(entry.time_seconds)
        })

    context = {
        'leaderboard_entries': formatted_entries
    }
    return render(request, 'game_app/leaderboard.html', context)