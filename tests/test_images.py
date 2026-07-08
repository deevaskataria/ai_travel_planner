import pytest
from unittest.mock import patch, MagicMock
import src.images

# Helper to reset state between tests
@pytest.fixture(autouse=True)
def reset_image_state():
    src.images.FETCHED_DESTINATIONS.clear()
    yield

def test_missing_api_key_returns_none_immediately():
    with patch('src.images.IMAGES_AVAILABLE', False):
        result = src.images.get_destination_image_url("Paris", "France")
        assert result is None

@patch('src.images.IMAGES_AVAILABLE', True)
@patch('src.images.UNSPLASH_ACCESS_KEY', 'fake_key')
@patch('src.images.st.session_state', {})
@patch('src.images.requests.get')
def test_get_image_handles_network_failure(mock_get):
    mock_get.side_effect = Exception("Network failure")
    
    result = src.images.get_destination_image_url("London", "UK")
    assert result is None
    assert mock_get.called

@patch('src.images.IMAGES_AVAILABLE', True)
@patch('src.images.UNSPLASH_ACCESS_KEY', 'fake_key')
@patch('src.images.st.session_state', {})
@patch('src.images.requests.get')
def test_get_image_handles_empty_results(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": []}
    mock_get.return_value = mock_resp
    
    result = src.images.get_destination_image_url("Nowhere", "Void")
    assert result is None
    assert mock_get.called
