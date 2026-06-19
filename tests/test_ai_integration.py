from unittest.mock import patch
from app import get_ai_insights, get_fallback_insights, cache

def test_fallback_insights_format():
    """Verify fallback insights follow the structured schema."""
    results = {
        "total_monthly_kg": 500,
        "total_yearly_tons": 6.0,
        "breakdown": {
            "travel": 100, "food": 100, "energy": 100, "waste": 50,
            "food_waste": 50, "goods": 50, "digital": 25, "healthcare": 25
        },
        "inputs": {
            "mode": "car", "distance": 15, "diet": "beef_heavy", "meals": 3,
            "cooking_style": "in_store", "electricity": 350, "energy_source": "grid_avg",
            "waste": 8, "food_waste": 2, "clothing": 10, "furniture": 1,
            "electronics": 2, "healthcare": 3, "streaming": 3
        }
    }
    insights = get_fallback_insights(results)
    
    assert "quick_wins" in insights
    assert "lifestyle_changes" in insights
    assert "systemic_actions" in insights
    assert "motivation" in insights
    
    assert len(insights["quick_wins"]) >= 1
    assert len(insights["lifestyle_changes"]) >= 1
    assert len(insights["systemic_actions"]) >= 1
    
    # Motivation assertions
    assert "trees_equivalent" in insights["motivation"]
    assert "cars_equivalent" in insights["motivation"]
    assert "yearly_goal" in insights["motivation"]

@patch('app.client')
def test_get_ai_insights_fallback_when_no_client(mock_client):
    import app
    original_client = app.client
    app.client = None
    
    results = {
        "total_monthly_kg": 500,
        "total_yearly_tons": 6.0,
        "breakdown": {
            "travel": 100, "food": 100, "energy": 100, "waste": 50,
            "food_waste": 50, "goods": 50, "digital": 25, "healthcare": 25
        },
        "inputs": {
            "mode": "car", "distance": 15, "diet": "beef_heavy", "meals": 3,
            "cooking_style": "in_store", "electricity": 350, "energy_source": "grid_avg",
            "waste": 8, "food_waste": 2, "clothing": 10, "furniture": 1,
            "electronics": 2, "healthcare": 3, "streaming": 3
        }
    }
    
    insights = get_ai_insights(results)
    assert insights == get_fallback_insights(results)
    
    app.client = original_client

@patch('app.client')
def test_get_ai_insights_caching(mock_client):
    """Test that caching prevents duplicate API calls and stores schema correctly."""
    import app
    cache.clear()

    # Create mock completion content representing schema
    mock_json = """
    {
      "quick_wins": [{"action": "Mock Win", "co2_savings": "10 kg", "cost_savings": "$5", "difficulty": "easy", "time_frame": "immediate"}],
      "lifestyle_changes": [{"action": "Mock Life", "co2_savings": "50 kg", "cost_savings": "$10", "difficulty": "medium", "time_frame": "3 months"}],
      "systemic_actions": [{"action": "Mock Sys", "co2_savings": "100 kg", "cost_savings": "$50", "difficulty": "hard", "time_frame": "1 year"}],
      "motivation": {"trees_equivalent": 10, "cars_equivalent": 0.5, "yearly_goal": "Goal", "progress_tracking": "Track"}
    }
    """

    class MockMessage:
        content = mock_json
    class MockChoice:
        message = MockMessage()
    class MockCompletion:
        choices = [MockChoice()]

    mock_client.chat.completions.create.return_value = MockCompletion()
    
    results = {
        "total_monthly_kg": 500,
        "total_yearly_tons": 6.0,
        "breakdown": {
            "travel": 100, "food": 100, "energy": 100, "waste": 50,
            "food_waste": 50, "goods": 50, "digital": 25, "healthcare": 25
        },
        "inputs": {
            "mode": "car", "distance": 15, "diet": "beef_heavy", "meals": 3,
            "cooking_style": "in_store", "electricity": 350, "energy_source": "grid_avg",
            "waste": 8, "food_waste": 2, "clothing": 10, "furniture": 1,
            "electronics": 2, "healthcare": 3, "streaming": 3
        }
    }

    insights1 = get_ai_insights(results)
    insights2 = get_ai_insights(results)

    assert insights1 == insights2
    assert insights1["quick_wins"][0]["action"] == "Mock Win"
    mock_client.chat.completions.create.assert_called_once()
