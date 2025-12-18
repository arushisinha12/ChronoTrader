# ChronoTrader ⏳🚀

**ChronoTrader** (Temporal Trader) is a Django-based strategy game where you play as a time-traveling merchant. Your goal is to navigate through different historical eras, exploiting market fluctuations to amass wealth and acquire the necessary **Temporal Fuel (Gold Coins)** to stabilize the timeline.

## 🎮 Gameplay Mechanics
- **Time Travel:** Jump between eras (e.g., Stone Age, Medieval, Future). Each jump costs **50 Credits**.
- **Market Arbitrage:** Prices for items change drastically across eras. A "Rubber Duck" might be worthless in 10,000 BC but a rare artifact in the future!
- **Objective:** Collect enough **Gold Coins** (Fuel) to win.
- **Risk:** If your credits drop below the cost of a time jump before you reach your goal, you become stranded in time (Game Over).
- **Leaderboard:** Compete for the fastest completion time.

## 🛠️ Installation & Setup
1. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv.  #python for some systems
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install django
   ```
3. **Prepare the Database**:
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```
4. **Run the Server**:
   ```bash
   python3 manage.py runserver
   ```
5. **Play**: Open [http://127.0.0.1:8000/console/](http://127.0.0.1:8000/console/) in your browser.

## 🌍 Live Demo
Play online: [https://chronotrader.pythonanywhere.com/console/](https://chronotrader.pythonanywhere.com/console/)

## 💻 Tech Stack
- **Backend:** Python, Django
- **Database:** SQLite
- **Frontend:** Django Templates, HTML/CSS

---
*Will you master the timeline or get lost in history?*