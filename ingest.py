import asyncio
import websockets
import json
import sqlite3
from datetime import datetime
import pandas as pd # We'll use pandas to check the DB

# --- Database Setup ---
DB_NAME = 'trades.db'

def create_database_table():
    """Establishes connection and creates the ticks table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            symbol TEXT,
            price REAL,
            size REAL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' and table 'ticks' are ready.")

# --- Data Handling ---
def normalize_trade_data(symbol, data):
    """Normalizes the incoming JSON trade data into a tuple for DB insertion."""
    try:
        # 'T' is the trade time (Unix timestamp in ms)
        trade_time = datetime.fromtimestamp(data['T'] / 1000).isoformat()
        return (
            trade_time,
            symbol,
            float(data['p']), # Price
            float(data['q'])  # Quantity/Size
        )
    except Exception as e:
        print(f"Error normalizing data: {e} | Data: {data}")
        return None

# --- WebSocket Connection ---
async def subscribe_to_trades(symbol, db_conn):
    """
    Connects to the Binance WebSocket for a specific symbol.
    Normalizes data and inserts it into the SQLite database.
    """
    url = f"wss://fstream.binance.com/ws/{symbol.lower()}@trade"
    
    while True: # Add a loop for automatic reconnection
        try:
            async with websockets.connect(url) as ws:
                print(f"WebSocket connected to: {symbol}")
                while True:
                    try:
                        message = await ws.recv()
                        data = json.loads(message)
                        
                        # We only care about the 'trade' event
                        if data.get('e') == 'trade':
                            normalized_tick = normalize_trade_data(symbol, data)
                            
                            if normalized_tick:
                                # Write to database
                                c = db_conn.cursor()
                                c.execute("INSERT INTO ticks (ts, symbol, price, size) VALUES (?, ?, ?, ?)", normalized_tick)
                                db_conn.commit()
                                
                                # Print to console to show it's working
                                print(f"TRADE [{symbol}]: {normalized_tick[2]} @ {normalized_tick[3]}")
                                
                    except websockets.exceptions.ConnectionClosed:
                        print(f"Connection closed for {symbol}. Reconnecting...")
                        break # Break inner loop to trigger reconnection
                    except Exception as e:
                        print(f"Error processing message for {symbol}: {e}")

        except Exception as e:
            print(f"WebSocket connection error for {symbol}: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5) # Wait before trying to reconnect

# --- Main Execution ---
async def main():
    symbols_to_track = ['btcusdt', 'ethusdt']
    
    # Establish a single, persistent database connection
    db_conn = sqlite3.connect(DB_NAME)

    # Create tasks for each symbol subscription
    tasks = [subscribe_to_trades(sym, db_conn) for sym in symbols_to_track]
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # 1. Set up the database and table first
    create_database_table()
    
    # 2. Run the async event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping data ingestor...")
        # Note: The DB connection is managed within the async tasks
        # In a more complex app, you'd explicitly close it here.