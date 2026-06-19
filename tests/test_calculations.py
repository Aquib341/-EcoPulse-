import pytest
from app import calculate_emissions, FACTORS

def test_calculate_emissions_default():
    """Test calculations with empty data fall back to defaults."""
    data = {}
    results = calculate_emissions(data)
    
    assert results['inputs']['distance'] == 10.0
    assert results['inputs']['meals'] == 3.0
    assert results['inputs']['electricity'] == 300.0
    assert results['total_monthly_kg'] > 0
    assert results['total_yearly_tons'] > 0

def test_calculate_emissions_valid():
    """Test with specific valid mock user inputs."""
    data = {
        "mode": "car",
        "distance": "20",
        "diet": "vegan",
        "meals": "2",
        "cooking_style": "in_store",
        "electricity": "200",
        "energy_source": "solar",
        "waste": "15",
        "food_waste": "3",
        "clothing": "12",
        "furniture": "2",
        "electronics": "3",
        "healthcare": "4",
        "streaming": "4"
    }
    
    results = calculate_emissions(data)
    
    # 1. Travel: 20 * 30 * 0.304 = 182.4
    assert results['breakdown']['travel'] == pytest.approx(182.4)
    
    # 2. Food: 2 * 30 * 0.3 = 18.0
    assert results['breakdown']['food'] == pytest.approx(18.0)
    
    # 3. Energy: 200 * 0.05 = 10.0
    assert results['breakdown']['energy'] == pytest.approx(10.0)
    
    # 4. Waste: 15 * 4.33 * 1.5 = 97.425 -> rounded is 97.43
    assert results['breakdown']['waste'] == pytest.approx(97.43, abs=0.1)
    
    # 5. Food Waste: 3 * 4.33 * 2.0 = 25.98
    assert results['breakdown']['food_waste'] == pytest.approx(25.98, abs=0.1)
    
    # 6. Goods: (12*5.0 + 2*50.0 + 3*20.0)/12 = (60 + 100 + 60)/12 = 220/12 = 18.33
    assert results['breakdown']['goods'] == pytest.approx(18.33, abs=0.1)
    
    # 7. Digital: 4 * 30 * 0.1 = 12.0
    assert results['breakdown']['digital'] == pytest.approx(12.0)
    
    # 8. Healthcare: 4 * 141.0 / 12 = 47.0
    assert results['breakdown']['healthcare'] == pytest.approx(47.0)

def test_calculate_emissions_invalid_fallbacks():
    """Test non-numeric inputs falling back to default values."""
    data = {
        "mode": "invalid_mode",       # falls back to car in FACTORS
        "distance": "non-numeric",   # falls back to 10.0
        "diet": "vegetarian",
        "meals": "invalid-meals",     # falls back to 3.0
        "electricity": "abc",         # falls back to 300.0
        "waste": "xyz"                # falls back to 10.0
    }
    
    results = calculate_emissions(data)
    
    # Travel: 10.0 * 30 * 0.304 = 91.2
    assert results['breakdown']['travel'] == pytest.approx(91.2)
    # Food: 3.0 * 30 * 0.5 = 45.0
    assert results['breakdown']['food'] == pytest.approx(45.0)
