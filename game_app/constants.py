import random

# --- GAME GOAL ---
# 🔑 Increased the goal slightly for the tighter economy
FUEL_GOAL = 5

# 🆕 FIXED CHRONOLOGICAL ORDER
ERA_ORDER = [
    "Ancient Rome",
    "The Aztec Empire",
    "Ming Dynasty China",
    "Renaissance France",
    "Victorian London",
]

# --- ERA DATA DEFINITION ---
ERAS = {
    "Ancient Rome": {
        "currency": "Denarii",
        # 🪙 Gold Coin is now the most expensive item to buy locally
        "trade_items": {"wine amphora": 35, "silk scroll": 220, "gold coin": 900}, 
        "prices": {"smartphone": 450, "candy bar": 15, "rubber duck": 45},
        "demand": {
            "feather cloak": 1000,
            "cacao bag": 350,
            "wine amphora": 5,
            "porcelain vase": 700,
        }
    },
    
    "The Aztec Empire": {
        "currency": "Cacao Beans",
        # 🪙 Gold Coin is now the most expensive item to buy locally
        "trade_items": {"obsidian knife": 90, "feather cloak": 400, "cacao bag": 30, "gold coin": 950}, 
        "prices": {"smartphone": 750, "candy bar": 60, "rubber duck": 110},
        "demand": {
            "silk scroll": 750,
            "wine amphora": 450,
            "gold coin": 1000,
            "perfume vial": 600,
        }
    },

    "Ming Dynasty China": {
        "currency": "Copper Cash",
        # 🪙 Gold Coin is now the most expensive item to buy locally
        "trade_items": {"porcelain vase": 900, "tea brick": 60, "printed book": 280, "gold coin": 1000}, 
        "prices": {"smartphone": 900, "candy bar": 35, "rubber duck": 140},
        "demand": {
            "telescope": 950,
            "obsidian knife": 800,
            "wine amphora": 150,
            "silk lace": 600,
            "coal sack": 120,
        }
    },
    
    "Renaissance France": {
        "currency": "Écu",
        # 🪙 Gold Coin is now the most expensive item to buy locally
        "trade_items": {"silk lace": 180, "perfume vial": 100, "telescope": 500, "gold coin": 1100}, 
        "prices": {"smartphone": 650, "candy bar": 25, "rubber duck": 90},
        "demand": {
            "cacao bag": 400,
            "feather cloak": 900,
            "silk scroll": 150,
            "wine amphora": 250,
            "printed book": 20,
        }
    },
    
    "Victorian London": {
        "currency": "Sterling Pound",
        # 🪙 Gold Coin is now the most expensive item to buy locally
        "trade_items": {"coal sack": 15, "steam engine part": 400, "newspaper bundle": 10, "gold coin": 1200}, 
        "prices": {"smartphone": 350, "candy bar": 10, "rubber duck": 25},
        "demand": {
            "porcelain vase": 1000,
            "printed book": 75,
            "tea brick": 900,
            "perfume vial": 250,
            "steam engine part": 20,
        }
    }
}

import random
import math
from .constants import ERAS, ERA_ORDER # Assuming ERAS and ERA_ORDER are defined in constants.py

def calculate_fluctuating_price(base_price, volatility):
    """
    Calculates a new price based on a base price and a volatility factor.
    The price fluctuates within +/- (volatility * 100)% of the base price.
    
    Args:
        base_price (int): The starting price.
        volatility (float): The percentage of fluctuation (e.g., 0.15 for 15%).
        
    Returns:
        int: The new, rounded, fluctuating price.
    """
    # Calculate the maximum deviation
    max_deviation = base_price * volatility
    
    # Generate a random fluctuation between -max_deviation and +max_deviation
    fluctuation = random.uniform(-max_deviation, max_deviation)
    
    # Calculate the new price
    new_price = base_price + fluctuation
    
    # Ensure price is at least 1 and round to the nearest integer
    return max(1, math.ceil(new_price))


def generate_era_prices(era_name):
    """
    Generates a dictionary of fluctuating buy prices and sell prices (demand) 
    for a given era based on the constants data structure.
    
    Returns:
        dict: {'buy_prices': {...}, 'sell_prices': {...}}
    """
    era_data = ERAS.get(era_name, ERAS[ERA_ORDER[0]])
    
    # --- Volatility Settings ---
    # Buy/Acquisition Volatility (lower)
    BUY_VOLATILITY = 0.15 
    # Demand/Sell Volatility (higher, since it's the target)
    SELL_VOLATILITY = 0.25 
    
    fluctuating_buy_prices = {}
    fluctuating_sell_prices = {}
    
    # 1. Generate Fluctuating BUY Prices (for Local Trade Items)
    for item_name, base_price in era_data['trade_items'].items():
        fluctuating_buy_prices[item_name] = calculate_fluctuating_price(
            base_price, BUY_VOLATILITY
        )

    # 2. Generate Fluctuating SELL Prices (for Local Demand Items)
    # The prices here are the high-value demand prices, so we apply higher volatility.
    for item_name, base_demand in era_data['demand'].items():
        fluctuating_sell_prices[item_name] = calculate_fluctuating_price(
            base_demand, SELL_VOLATILITY
        )
        
    # 3. Add Modern Items (which aren't trade items but could be sold if somehow acquired)
    # We apply the sell volatility to the base modern item prices.
    for item_name, base_price in era_data['prices'].items():
         fluctuating_sell_prices[item_name] = calculate_fluctuating_price(
            base_price, BUY_VOLATILITY # Lower volatility for modern items
        )

    return {
        'buy_prices': fluctuating_buy_prices,
        'sell_prices': fluctuating_sell_prices
    }