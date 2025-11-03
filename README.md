# Quant Developer Evaluation Assignment

This project is a complete, end-to-end analytical application built for the Quant Developer Evaluation Assignment. It implements a system that handles real-time data ingestion, persistent storage, quantitative analysis, and interactive visualization, all as specified in the project brief.

![Dashboard Screenshot](Screenshot.png)

---

## 🚀 Core Features

This application successfully implements all core requirements from the assignment:

* **Real-time Data Ingestion:** Connects directly to the Binance WebSocket stream (`btcusdt@trade`, `ethusdt@trade`) to ingest live tick data.
* **Persistent Storage:** All incoming tick data is stored in a local **SQLite** database (`trades.db`), which acts as a simple and robust data store.
* **Selectable Timeframes:** The frontend provides controls to sample and resample all analytics on-the-fly to **1s, 1m, or 5m** timeframes.
* **Quantitative Analytics:** The app computes all required analytics:
    * **Hedge Ratio** via OLS Regression
    * **Cointegrated Spread**
    * **Rolling Z-Score** of the spread
    * **ADF Test** for spread stationarity
    * **Rolling Correlation**
* **Interactive Visualization:** All analytics are plotted on interactive charts (supporting zoom, pan, and hover) using Streamlit and Altair.
* **Live Alerting:** A user-defined **Z-Score threshold** in the sidebar triggers a visible alert on the dashboard if breached.
* **Data Export:** A "Download CSV" button allows for the export of all processed, resampled, and computed analytics data.

---

## 🏛️ Architecture & Design Philosophy (40% Criterion)

The architecture was designed to meet the assignment's emphasis on **modularity, extensibility, and clarity**.

The system uses a **decoupled, two-process architecture**:

1.  **Process 1: `ingest.py` (The Ingestor)**
    * A standalone Python script using `websockets` and `sqlite3`.
    * **Responsibility:** Connects to the Binance WebSocket, parses trade messages, and writes raw tick data to the `trades.db` database.
    * This component is completely isolated.

2.  **Process 2: `app.py` (The Analytics Dashboard)**
    * A **Streamlit** application.
    * **Responsibility:** Runs the web server, reads data from `trades.db` (using `pandas`), performs all sampling and analytics (using `statsmodels` and `pandas`), and renders the interactive UI.

[cite_start]This design directly adheres to the **Design Philosophy** [cite: 55-64]:

* **Loosely Coupled:** The Ingestor and the Dashboard interact only through the database. The ingestor (data source) can be stopped, restarted, or modified (e.g., to add a different data feed) without ever stopping the analytics app, and vice-versa.
* **Extensibility:** This design makes it trivial to add new features. A new analytic can be added to `app.py` without touching ingestion. A new data source (e.g., a REST API feed) could be plugged in by modifying only `ingest.py` without changing a single line of the analytics code.
* **Clarity over Complexity:** Instead of a complex, single-file, or in-memory application, this two-process model is simple, readable, and robust. Using SQLite + Streamlit was a deliberate choice for rapid development and clarity while proving the architecture.

### Architecture Diagram

![Architecture Diagram](Architecture.png)

---

## 🛠️ Setup & Execution

**Prerequisites:**
* Python 3.9+

### 1. Clone the Repository
```bash
git clone https://github.com/PraveenBontha94/Praveen_CS22B2033
cd Praveen_CS22B2033
```

### 2. Create Virtual Environment & Install Dependencies
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install all required libraries
pip install -r requirements.txt
```

### 3. Run the Application (Requires 2 Terminals)

**In your FIRST terminal:**
Start the data ingestor. This will connect to Binance and create/populate the `trades.db` file.
```bash
python ingest.py
```

**In your SECOND terminal:**
Run the Streamlit frontend. This will automatically open the dashboard in your browser.
```bash
streamlit run app.py
```
The dashboard will initially show "Waiting for data..." and will auto-populate as data flows in from the ingestor.

---

## 📊 Analytics Methodology

This app provides the following analytics as requested:

* **OLS Hedge Ratio**: A linear regression is run between the two asset prices (ETH as Y, BTC as X). The `slope` (coefficient) of this regression is the hedge ratio, representing how many units of BTC are needed to hedge one unit of ETH.
* **Spread**: The spread is calculated as a market-neutral portfolio:
    `Spread = Price(ETH) - (Hedge_Ratio * Price(BTC))`
* **ADF Test**: The Augmented Dickey-Fuller test is a statistical test for stationarity. A low p-value (e.g., < 0.05) suggests the spread is "mean-reverting," which is a desirable property for pairs trading.
* **Z-Score**: This measures how many standard deviations the current spread is from its rolling mean. It is the primary signal for trading:
    `Z-Score = (Spread - Rolling_Mean(Spread)) / Rolling_StdDev(Spread)`
