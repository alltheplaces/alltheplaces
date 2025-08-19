"""
Test to verify that Japan's coordinates point to Tokyo administrative center.

This test addresses the issue where Japan's coordinates were pointing to
the middle of the ocean rather than to Tokyo's administrative center.
"""
import json
import sys
import os

# Add the locations directory to Python path if needed
if '/home/runner/work/alltheplaces/alltheplaces' not in sys.path:
    sys.path.insert(0, '/home/runner/work/alltheplaces/alltheplaces')


def test_japan_coordinates_point_to_tokyo():
    """Test that Japan's coordinates are properly located in Tokyo administrative area."""
    # Load coordinates directly from the JSON file
    coords_file = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'locations', 
        'searchable_points', 
        'country_coordinates.json'
    )
    
    with open(coords_file, 'r') as f:
        coords = json.load(f)
    
    # Find Japan's coordinates
    japan_coords = None
    for entry in coords:
        if entry['isocode'] == 'JP':
            japan_coords = entry
            break
    
    assert japan_coords is not None, "Japan coordinates not found"
    
    lon = float(japan_coords['lon'])
    lat = float(japan_coords['lat'])
    
    # Tokyo is approximately at 139.6917°E, 35.6895°N
    # The coordinates should be in the Tokyo metropolitan area
    expected_lon_min, expected_lon_max = 139.0, 140.5  # Tokyo area longitude range
    expected_lat_min, expected_lat_max = 35.0, 36.0    # Tokyo area latitude range
    
    assert expected_lon_min <= lon <= expected_lon_max, (
        f"Japan longitude {lon} is not in Tokyo area. "
        f"Expected range: [{expected_lon_min}, {expected_lon_max}]"
    )
    assert expected_lat_min <= lat <= expected_lat_max, (
        f"Japan latitude {lat} is not in Tokyo area. "
        f"Expected range: [{expected_lat_min}, {expected_lat_max}]"
    )
    
    # Also verify it's reasonably close to Tokyo center (within ~100km ≈ 1 degree)
    tokyo_lon, tokyo_lat = 139.6917, 35.6895
    lon_diff = abs(lon - tokyo_lon)
    lat_diff = abs(lat - tokyo_lat)
    
    assert lon_diff <= 1.0, (
        f"Japan longitude {lon} is too far from Tokyo center ({tokyo_lon}). "
        f"Difference: {lon_diff}°"
    )
    assert lat_diff <= 1.0, (
        f"Japan latitude {lat} is too far from Tokyo center ({tokyo_lat}). "
        f"Difference: {lat_diff}°"
    )


def test_coordinates_not_in_ocean():
    """Test that the previous ocean coordinates are no longer used."""
    coords_file = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'locations', 
        'searchable_points', 
        'country_coordinates.json'
    )
    
    with open(coords_file, 'r') as f:
        coords = json.load(f)
    
    # Find Japan's coordinates
    japan_coords = None
    for entry in coords:
        if entry['isocode'] == 'JP':
            japan_coords = entry
            break
    
    assert japan_coords is not None, "Japan coordinates not found"
    
    lon = float(japan_coords['lon'])
    lat = float(japan_coords['lat'])
    
    # Ensure we're not using the old problematic coordinates
    old_lon, old_lat = 136.0, 35.0
    
    # The coordinates should be different from the old ones that were pointing to ocean
    assert lon != old_lon or lat != old_lat, (
        f"Japan coordinates ({lon}, {lat}) are still using the old ocean coordinates"
    )


if __name__ == "__main__":
    test_japan_coordinates_point_to_tokyo()
    test_coordinates_not_in_ocean()
    print("✓ All Japan coordinates tests passed!")