import os
import json
import hashlib
from flask import Flask, render_template, request, session, jsonify
from flask_caching import Cache
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-dev-secret-key")

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 3600})

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None
    print("WARNING: GROQ_API_KEY not found in environment. AI insights will use fallback.")

# Emission Factors (Deterministic, based on factsheet data)
FACTORS = {
    "travel": {
        "car": 0.304,         # 0.67 lbs/mile converted to kg/km
        "flight": 0.186,      # 0.41 lbs/mile converted to kg/km
        "car_electric": 0.0,  # EV with grid average
        "bus": 0.08,
        "motorbike": 0.05
    },
    "food": {
        "beef_heavy": 12.5,   # 36x plant-based
        "chicken": 4.2,       # kg CO2e/kg equivalent or per meal scale
        "vegetarian": 0.5,
        "vegan": 0.3,
        "dairy": 2.0
    },
    "energy": {
        "grid_avg": 0.363,    # 0.8 lbs/kWh converted
        "coal": 1.02,         # 2.25 lbs/kWh converted
        "natural_gas": 0.39,  # 0.86 lbs/kWh converted
        "solar": 0.05,        # Upstream emissions
        "wind": 0.02          # Upstream emissions
    },
    "goods": {
        "clothing": 5.0,      # kg CO2e per item
        "furniture": 50.0,    # kg CO2e per item
        "electronics": 20.0   # kg CO2e per item
    },
    "waste": {
        "general": 1.5,       # kg CO2e per kg waste
        "food": 2.0           # kg CO2e per kg food waste
    },
    "digital": 0.1,           # kg CO2e per streaming hour
    "healthcare": 141.0       # kg CO2e per visit (1692 kg/capita per year / 12)
}

def calculate_emissions(data):
    """
    Calculate carbon emissions based on advanced user inputs and return a detailed breakdown.
    Formulas are monthly calculations:
    - Travel: Daily Distance * 30 days * Travel Factor
    - Food: Meals/Day * 30 days * Diet Factor * (0.67 if Meal Kits else 1.0)
    - Energy: Monthly kWh * Energy Factor
    - Waste: Weekly Waste * 4.3 weeks * General Waste Factor
    - Food Waste: Weekly Food Waste * 4.3 weeks * Food Waste Factor
    - Goods: (Clothing * 5.0 + Furniture * 50.0 + Electronics * 20.0) / 12
    - Digital: Streaming Hours/Day * 30 days * Digital Factor
    - Healthcare: Visits/Year * 141.0 / 12
    """
    try:
        distance = float(data.get("distance", 10))
        meals = float(data.get("meals", 3))
        electricity = float(data.get("electricity", 300))
        waste = float(data.get("waste", 10))
        food_waste = float(data.get("food_waste", 2))
        clothing = float(data.get("clothing", 5))
        furniture = float(data.get("furniture", 1))
        electronics = float(data.get("electronics", 1))
        healthcare = float(data.get("healthcare", 2))
        streaming = float(data.get("streaming", 2))
    except ValueError:
        distance = 10.0
        meals = 3.0
        electricity = 300.0
        waste = 10.0
        food_waste = 2.0
        clothing = 5.0
        furniture = 1.0
        electronics = 1.0
        healthcare = 2.0
        streaming = 2.0

    mode = data.get("mode", "car")
    diet = data.get("diet", "beef_heavy")
    energy_source = data.get("energy_source", "grid_avg")
    cooking_style = data.get("cooking_style", "in_store")

    # Perform calculations
    travel_emission = distance * 30 * FACTORS["travel"].get(mode, FACTORS["travel"]["car"])
    
    # Meal kits reduce food prep GHG emissions by 33%
    food_base = meals * 30 * FACTORS["food"].get(diet, FACTORS["food"]["beef_heavy"])
    food_emission = food_base * 0.67 if cooking_style == "meal_kits" else food_base
    
    energy_emission = electricity * FACTORS["energy"].get(energy_source, FACTORS["energy"]["grid_avg"])
    
    # Monthly waste is weekly * 4.33 weeks
    waste_emission = waste * 4.33 * FACTORS["waste"]["general"]
    food_waste_emission = food_waste * 4.33 * FACTORS["waste"]["food"]
    
    goods_emission = (clothing * FACTORS["goods"]["clothing"] + 
                      furniture * FACTORS["goods"]["furniture"] + 
                      electronics * FACTORS["goods"]["electronics"]) / 12.0
                      
    digital_emission = streaming * 30 * FACTORS["digital"]
    
    healthcare_emission = (healthcare * FACTORS["healthcare"]) / 12.0

    total = (travel_emission + food_emission + energy_emission + 
             waste_emission + food_waste_emission + goods_emission + 
             digital_emission + healthcare_emission)

    return {
        "total_monthly_kg": round(total, 2),
        "total_yearly_tons": round((total * 12) / 1000, 2),
        "breakdown": {
            "travel": round(travel_emission, 2),
            "food": round(food_emission, 2),
            "energy": round(energy_emission, 2),
            "waste": round(waste_emission, 2),
            "food_waste": round(food_waste_emission, 2),
            "goods": round(goods_emission, 2),
            "digital": round(digital_emission, 2),
            "healthcare": round(healthcare_emission, 2)
        },
        "inputs": {
            "mode": mode,
            "distance": distance,
            "diet": diet,
            "meals": meals,
            "electricity": electricity,
            "energy_source": energy_source,
            "waste": waste,
            "food_waste": food_waste,
            "clothing": clothing,
            "furniture": furniture,
            "electronics": electronics,
            "healthcare": healthcare,
            "cooking_style": cooking_style,
            "streaming": streaming
        }
    }

def get_ai_insights(results):
    """
    Generate personalized recommendations using the Groq API.
    Response must conform to the 7-recommendation JSON schema.
    """
    if not client:
        return get_fallback_insights(results)

    # Cache key based on input values
    input_str = json.dumps(results["inputs"], sort_keys=True)
    cache_key = hashlib.md5(input_str.encode()).hexdigest()

    cached_insights = cache.get(cache_key)
    if cached_insights:
        return cached_insights

    total_yearly = results["total_yearly_tons"]
    comparison = round((total_yearly / 17.6) * 100, 1)

    prompt = f"""ACT AS: Expert Carbon Footprint Coach with 10+ years experience in environmental science and behavioral psychology

USER DATA:
- Individual Yearly Footprint: {total_yearly} t CO2e/year
- Monthly Footprint Breakdown (kg CO2e):
  • Transportation: {results['breakdown']['travel']} kg ({round(results['breakdown']['travel']/results['total_monthly_kg']*100, 1)}%)
  • Food/Diet: {results['breakdown']['food']} kg ({round(results['breakdown']['food']/results['total_monthly_kg']*100, 1)}%)
  • Household Energy: {results['breakdown']['energy']} kg ({round(results['breakdown']['energy']/results['total_monthly_kg']*100, 1)}%)
  • General Waste: {results['breakdown']['waste']} kg
  • Food Waste: {results['breakdown']['food_waste']} kg
  • Goods & Services: {results['breakdown']['goods']} kg
  • Digital Usage: {results['breakdown']['digital']} kg
  • Healthcare: {results['breakdown']['healthcare']} kg

BENCHMARKS:
- U.S. Average: 17.6 t CO2e/yr (User is at {comparison}% of average)
- Global Average: 6.6 t CO2e/yr
- Paris 2030 Target: 2.3 t CO2e/yr
- Top 1% Emitters: 74 t CO2e/yr

USER BEHAVIOR HIGHLIGHTS:
- Travels by {results['inputs']['mode']} for {results['inputs']['distance']} km/day.
- Diet Type: {results['inputs']['diet']}, Meals/day: {results['inputs']['meals']}. Cooking style: {results['inputs']['cooking_style']}.
- Monthly Electricity: {results['inputs']['electricity']} kWh using {results['inputs']['energy_source']}.
- Weekly Food Waste: {results['inputs']['food_waste']} kg. Digital Streaming: {results['inputs']['streaming']} hours/day.

YOUR TASK: Generate a comprehensive, personalized action plan with EXACTLY 7 recommendations formatted strictly as a JSON object:

{{
  "quick_wins": [
    {{
      "action": "string description including behavioral savings",
      "co2_savings": "kg/year",
      "cost_savings": "$/year",
      "difficulty": "easy/medium",
      "time_frame": "immediate/1 month"
    }}
  ],
  "lifestyle_changes": [
    {{
      "action": "string description including diet or transit swap details",
      "co2_savings": "kg/year",
      "cost_savings": "$/year",
      "difficulty": "medium/hard",
      "time_frame": "3 months/6 months"
    }}
  ],
  "systemic_actions": [
    {{
      "action": "string description involving solar, EV or insulation upgrades",
      "co2_savings": "kg/year",
      "cost_savings": "$/year",
      "difficulty": "hard/expert",
      "time_frame": "1-2 years"
    }}
  ],
  "motivation": {{
    "trees_equivalent": number,
    "cars_equivalent": number,
    "yearly_goal": "string motivational framing",
    "progress_tracking": "string detail"
  }}
}}

ADDITIONAL FACTS TO INTEGRATE IN VALUE ESTIMATES AND ACTIONS:
- Every 5 mph over 50 costs additional $0.27-$0.54/gal
- LED bulbs save $200/year (around 500 kg CO2e)
- Cold water washing saves 70 lbs (32 kg) CO2e/load
- Standby power costs $100/year
- Meal kits reduce GHG by 33% vs in-store
- Solar-reflective roofs reduce cooling energy by 27%
- Refurbished furniture cuts emissions by up to 85%
- Streaming 12 hrs/day exceeds 50% of individual 2-ton footprint
- Agriculture is responsible for 50% of CH4, 66% of N2O
- 90% of fashion emissions occur overseas
- NATO 2% GDP spending would emit 2 Bt CO2e/yr

RESPONSE FORMAT: Valid JSON only. Do not wrap in markdown or include extra text."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON objects containing the exact requested fields without markdown wrappers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content.strip()
        
        # Strip potential markdown wrapping
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        
        # Verify schema presence
        if "quick_wins" in parsed and "lifestyle_changes" in parsed and "systemic_actions" in parsed:
            cache.set(cache_key, parsed)
            return parsed
        else:
            return get_fallback_insights(results)

    except Exception as e:
        print(f"Error fetching AI insights: {e}")
        return get_fallback_insights(results)

def get_fallback_insights(results):
    """Fallback structured insights matching the JSON schema."""
    inputs = results["inputs"]
    
    # Customize fallback values based on user inputs
    travel_tip = "Drive at the speed limit. Every 5 mph over 50 costs an extra $0.27-$0.54 per gallon."
    if inputs["mode"] == "car_electric":
        travel_tip = "Ensure your EV is charged using solar or green grid plans to reach true zero-emissions."
        
    diet_tip = "Swap one beef meal per week to chicken or vegetarian. Beef causes 36x more CO2e than plant options."
    if inputs["diet"] == "vegetarian" or inputs["diet"] == "vegan":
        diet_tip = "Continue your low-impact plant-based diet and encourage household members to join."

    energy_tip = "Switch to LED lightbulbs. This easy change saves about 500 kg CO2e and $200 per year."
    if inputs["energy_source"] in ["solar", "wind"]:
        energy_tip = "Maintain your clean energy sources and look into adding battery storage to buffer peak hours."

    digital_tip = "Stream content in SD/HD rather than Ultra 4K to decrease data center energy consumption."
    if inputs["streaming"] > 4:
        digital_tip = f"Your {inputs['streaming']} hours of streaming daily is a hidden carbon cost. Unplug idle routers to save $100/yr."

    return {
        "quick_wins": [
            {
                "action": energy_tip,
                "co2_savings": "500 kg/year",
                "cost_savings": "$200/year",
                "difficulty": "easy",
                "time_frame": "immediate"
            },
            {
                "action": "Unplug standby electronics and use smart power strips to eliminate phantom loads.",
                "co2_savings": "200 kg/year",
                "cost_savings": "$100/year",
                "difficulty": "easy",
                "time_frame": "immediate"
            },
            {
                "action": "Wash laundry in cold water. Cold water washing saves 70 lbs (32 kg) CO2e/load.",
                "co2_savings": "150 kg/year",
                "cost_savings": "$40/year",
                "difficulty": "easy",
                "time_frame": "1 month"
            }
        ],
        "lifestyle_changes": [
            {
                "action": diet_tip,
                "co2_savings": "450 kg/year",
                "cost_savings": "$300/year",
                "difficulty": "medium",
                "time_frame": "3 months"
            },
            {
                "action": travel_tip,
                "co2_savings": "350 kg/year",
                "cost_savings": "$180/year",
                "difficulty": "medium",
                "time_frame": "3 months"
            },
            {
                "action": digital_tip,
                "co2_savings": "80 kg/year",
                "cost_savings": "$50/year",
                "difficulty": "medium",
                "time_frame": "1 month"
            }
        ],
        "systemic_actions": [
            {
                "action": "Install rooftop solar panels or switch to a certified 100% renewable energy provider.",
                "co2_savings": "2200 kg/year",
                "cost_savings": "$800/year",
                "difficulty": "expert",
                "time_frame": "1-2 years"
            }
        ],
        "motivation": {
            "trees_equivalent": int(results["total_monthly_kg"] * 12 / 48),
            "cars_equivalent": round(results["total_yearly_tons"] / 4.6, 1),
            "yearly_goal": "Your goal: Reach under 2.3 tons CO2e/year by implementing these action steps.",
            "progress_tracking": "Track your weekly waste reductions and count vegetarian meals to see your level grow!"
        }
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form
        results = calculate_emissions(data)
        
        # Manage gamification/streak
        if 'streak' not in session:
            session['streak'] = 1
        else:
            session['streak'] += 1
            
        insights = get_ai_insights(results)
        
        return render_template("index.html", results=results, insights=insights, streak=session.get('streak'))

    # GET request: render default page
    return render_template("index.html", results=None, streak=session.get('streak', 0))

@app.route("/api/benchmark", methods=["GET"])
def get_benchmarks():
    """API endpoint to retrieve benchmarks for comparison charts."""
    return jsonify({
        "us_average": 17.6,
        "global_average": 6.6,
        "paris_target": 2.3,
        "top_1_percent": 74.0
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
