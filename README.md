# EcoPulse 🌿 — Carbon Footprint Dashboard & AI Coach

EcoPulse is a premium, data-driven Carbon Footprint Awareness & Behavioral Nudge Platform. By combining precise emission factors with client-side What-If simulations, dynamic Chart.js analytics, a gamified achievements system, and personalized AI coaching (powered by Groq / Llama 3.1), EcoPulse empowers users to transition from climate awareness to measurable action.

---

## 📊 Benchmarks & Science

According to global environmental statistics, the average emissions per capita are highly unequal. EcoPulse is built to contextualize individual impacts against international benchmarks:

*   **U.S. Average:** 17.6 Tons CO₂e/year
*   **Global Average:** 6.6 Tons CO₂e/year
*   **Paris 2030 Target:** Under 2.3 Tons CO₂e/year (Necessary to keep global warming below 1.5°C)
*   **Top 1% Global Emitters:** 74.0 Tons CO₂e/year

---

## 🚀 Key Features

### 1. Multi-Category Advanced Assessment
Instead of basic estimates, EcoPulse calculates footprint values using 14 advanced inputs grouped into:
*   **Transportation:** Travel mode (including EVs, passenger cars, bikes, flights) and daily distance.
*   **Diet & Food Prep:** Diet types (Heavy Beef, Chicken, Vegetarian, Vegan, Dairy) and cooking styles (In-Store Shopping vs. Meal Kits which reduce emissions by 33%).
*   **Energy & Waste:** Specific household fuel sources (Coal, Gas, Solar, Wind, Grid Average) and separated general and organic food waste.
*   **Consumption & Lifestyle:** Clothing, tech devices, and furniture purchases per year, along with daily digital streaming hours and healthcare visits.

### 2. High-Fidelity Analytics (Chart.js)
*   **Emission Breakdown (Doughnut Chart):** Displays the proportional footprint contribution across Travel, Diet, Energy, Waste, Goods, Digital, and Healthcare.
*   **Benchmark Tracker (Horizontal Bar Chart):** Visually positions the user's footprint against U.S., Global, Paris 2030, and Top 1% benchmarks.

### 3. Advanced What-If Simulator
Includes real-time client-side calculations modeling various behavioral swaps:
*   *Drive at Speed Limit:* Reduces travel emissions by 10% (saves fuel).
*   *Switch to LED Bulbs:* Flat reduction of 500 kg CO₂e/year (saves $200/year).
*   *Unplug Standby Power:* Flat reduction of 200 kg CO₂e/year (saves $100/year).
*   *Wash Laundry in Cold Water:* Saves 32 kg CO₂e/year.
*   *Refurbished Furniture:* Cuts furniture purchase footprint by 85%.
*   *Solar-Reflective Roof:* Saves 27% on cooling electricity.
*   *Forest Trees & Cars Equivalencies:* Dynamically updates yearly forest trees needed and passenger cars equivalents.

### 4. Custom AI Coach & Structured Responses
*   Integrates with the **Groq SDK (Llama 3.1 70B)** to evaluate user data and issue 7 specific recommendations categorized under **Quick Wins**, **Lifestyle Changes**, and **Systemic Actions**.
*   Features a robust, local python-based JSON schema fallback engine to render structured coaching suggestions if API limits are reached.

### 5. Gamified Achievements
A dynamic badges panel that unlocks badges based on calculation metrics:
*   🏆 **Paris Agreement Achiever:** Footprint below 2.3 Tons/yr.
*   💡 **Energy Wizard:** Using green energy sources (Solar/Wind) or household energy below 50 kg/mo.
*   🥗 **Plant-Based Pioneer:** Selecting vegetarian or vegan diet plans.
*   🚶 **Walking Warrior:** Keep transportation footprint under 50 kg/mo.
*   ♻️ **Waste Minimalist:** Food waste below 2.27 kg (5 lbs) per week.
*   📱 **Digital Minimalist:** Daily streaming under 2 hours.

---

## 🛠️ Technology Stack

*   **Backend:** Python 3.9+, Flask 2.3.x, Flask-Caching, python-dotenv
*   **AI Engine:** Groq Cloud API (Llama 3.1 70B model)
*   **Frontend:** HTML5, Vanilla CSS3 (Custom Glassmorphism, animations, responsive design), Vanilla Javascript, Chart.js CDN, Font Awesome
*   **Testing:** Pytest

---

## 📁 Repository Structure

```text
EcoPulse/
├── app.py                 # Flask server, calculations, & AI Coach prompts
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
├── templates/
│   └── index.html        # Glassmorphism HTML5 template & Chart.js hooks
├── static/
│   ├── css/
│   │   └── style.css     # Premium styling, variables, and dark mode rules
│   └── js/
│       └── simulator.js  # Live What-If mathematical model & chart initializers
└── tests/
    ├── test_calculations.py     # Assessment validation suite
    └── test_ai_integration.py  # Cache & AI schema validation suite
```

---

## ⚙️ Setup & Installation

### 1. Initialize Virtual Environment
Navigate to the directory and set up Python's virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Config
Copy the example configuration:
```bash
cp .env.example .env
```
Add your `GROQ_API_KEY` inside `.env`. If not provided, EcoPulse will use its built-in rule-based fallback recommendations.

### 4. Run the Dev Server
```bash
python3 app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

### 5. Running Automated Tests
Verify calculations and AI formats:
```bash
python3 -m pytest tests/
```

---

## 🌐 Deploy to GitHub (Workflow)

Follow this step-by-step process to upload EcoPulse to your GitHub account:

### 1. Initialize Git in Local Directory
```bash
git init
```

### 2. Create `.gitignore`
Ensure sensitive details (`.env`, `venv/`, cache directories) are ignored:
```bash
echo "venv/\n.env\n__pycache__/\n.pytest_cache/\n*.pyc" > .gitignore
```

### 3. Stage & Commit Files
```bash
git add .
git commit -m "feat: rebuild EcoPulse with advanced carbon calculations and Chart.js dashboards"
```

### 4. Configure Remote Repository
Create a new blank repository on GitHub (do **not** check "Initialize this repository with a README"), and connect your local repository:
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### 5. Push to GitHub
```bash
git push -u origin main
```
