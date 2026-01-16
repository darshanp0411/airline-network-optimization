# ✈️ Airline Network Strategist & Demand Forecaster

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b)
![Status](https://img.shields.io/badge/Status-Portfolio_Project-green)

## 📖 Overview
This project is a full-stack data science application designed to simulate the decision-making process of an **Airline Network Planner**. 

Using real-world data from the **Bureau of Transportation Statistics (BTS)**, the application ingests millions of flight records to identify underserved routes, calculate per-flight profitability, and forecast future passenger demand using Machine Learning.

It is designed to solve two core business problems:
1.  **Network Optimization:** Which current routes are bleeding money, and which are "Cash Cows"?
2.  **Demand Forecasting:** Predicting passenger volume for the next 12 months while accounting for seasonality and market recovery.

## 🚀 Key Features

### 1. 💰 Route Profitability Engine
* Calculates **P&L (Profit and Loss)** for every route from a specific hub.
* Uses a **Boeing 737 Operating Cost Model** (Fuel Burn + Crew Costs).
* Applies a **Yield Decay Curve** to estimate revenue based on flight distance.
* *Outcome:* Identifies the most profitable routes in the network.

### 2. 🔥 Load Factor Efficiency Map
* Visualizes the relationship between **Frequency** (Flights per day) and **Load Factor** (How full the plane is).
* Highlights "Underserved" opportunities (High Load Factor, Low Frequency) where the airline should add capacity.

### 3. 🤖 AI Demand Forecaster (Covid-Aware)
* **Model:** Random Forest Regressor.
* **Strategy:** Implements a "Donut Hole" training approach. It trains on pre-pandemic data (2017-2019) for seasonality and post-pandemic data (2022-2024) for current volume, deliberately excluding the 2020-2021 structural break to improve accuracy.
* **Output:** Generates a 12-month forward-looking demand curve.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Interactive Dashboard)
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn (Random Forest)
* **Visualization:** Plotly Express

## 📂 Data Source
This project uses **T-100 Segment Data** from the US Department of Transportation.
* **Source:** [BTS Transtats Database](https://www.transtats.bts.gov/)
* **Data Range:** 2017–2024 (Multi-year analysis).

## ⚙️ Installation & Usage

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR-USERNAME/airline-network-optimization.git](https://github.com/YOUR-USERNAME/airline-network-optimization.git)
    cd airline-network-optimization
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Data**
    * Create a folder named `airline_data` in the root directory.
    * Place your BTS `.csv` files inside this folder (e.g., `2023_data.csv`, `2024_data.csv`).

4.  **Run the App**
    ```bash
    streamlit run app.py
    ```

## 🧠 Methodology Details

### The Profit Formula
The application estimates profit per flight using the following assumptions (customizable in the sidebar):
$$ Profit = (Pax \times AvgFare) - (BlockHours \times HourlyCost) $$
* **Avg Fare:** Derived from a distance-based yield curve ($0.60/mi short-haul $\to$ $0.15/mi long-haul).
* **Hourly Cost:** Combined cost of Fuel (850 gal/hr) + Crew/Maint ($5,500/hr).

### The "Donut Hole" Forecasting Strategy
Forecasting airline data is difficult due to the COVID-19 anomaly.
* **Standard models** fail because they interpret 2020 as a "trend."
* **My Solution:** The script dynamically filters the training set:
    `clean_data = route_data[~route_data['YEAR'].isin([2020, 2021])]`
    This allows the AI to learn "Normal Seasonality" from 2019 and "Current Demand" from 2024 without being confused by the lockdowns.

## 📸 Screenshots


## 📜 License
MIT License
