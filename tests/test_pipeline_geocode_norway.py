from unittest.mock import MagicMock, patch

import requests
from scrapy import Spider
from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature, get_lat_lon
from locations.pipelines.geocode_norway import GeocodeNorwayPipeline


def get_objects(country=None, lat=None, lon=None, geometry=None, **address_fields):
    """Helper to create test objects."""
    spider = DefaultSpider()
    spider.crawler = get_crawler()

    item_fields = {"country": country}
    if lat is not None:
        item_fields["lat"] = lat
    if lon is not None:
        item_fields["lon"] = lon
    if geometry is not None:
        item_fields["geometry"] = geometry
    item_fields.update(address_fields)

    return (
        Feature(**item_fields),
        GeocodeNorwayPipeline(),
        spider,
    )


def get_stat(spider: Spider, key: str) -> int | None:
    """Helper to safely get a stat value from spider crawler stats."""
    if spider.crawler and spider.crawler.stats:
        return spider.crawler.stats.get_value(key)
    return None


def mock_geonorge_response(lat=59.9139, lon=10.7522):
    """Create a mock successful Geonorge API response."""
    return {
        "adresser": [
            {
                "representasjonspunkt": {
                    "lat": lat,
                    "lon": lon,
                }
            }
        ]
    }


class TestSkipConditions:
    """Tests for conditions where geocoding should be skipped."""

    def test_skip_non_norwegian_country(self):
        """Pipeline should skip items not in Norway."""
        item, pipeline, spider = get_objects(
            country="SE",
            street="Testgatan",
            housenumber="1",
            postcode="12345",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        # Should not make any API calls
        mock_get.assert_not_called()
        assert get_lat_lon(result) is None

    def test_skip_empty_country(self):
        """Pipeline should skip items without a country."""
        item, pipeline, spider = get_objects(
            country=None,
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None

    def test_skip_existing_lat_lon(self):
        """Pipeline should skip items that already have lat/lon coordinates."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            street="Karl Johans gate",
            housenumber="1",
            postcode="0154",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        # Original coordinates should be preserved
        assert result.get("lat") == 59.9139
        assert result.get("lon") == 10.7522

    def test_skip_existing_geometry(self):
        """Pipeline should skip items that already have Point geometry."""
        item, pipeline, spider = get_objects(
            country="NO",
            geometry={"type": "Point", "coordinates": [10.7522, 59.9139]},
            street="Karl Johans gate",
            housenumber="1",
            postcode="0154",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("geometry") == {"type": "Point", "coordinates": [10.7522, 59.9139]}


class TestInsufficientAddressData:
    """Tests for cases with insufficient address data for geocoding."""

    def test_insufficient_only_street(self):
        """Street alone is insufficient for geocoding."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1

    def test_insufficient_only_postcode(self):
        """Postcode alone is insufficient for geocoding."""
        item, pipeline, spider = get_objects(
            country="NO",
            postcode="0154",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1

    def test_insufficient_only_city(self):
        """City alone is insufficient for geocoding."""
        item, pipeline, spider = get_objects(
            country="NO",
            city="Oslo",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1

    def test_insufficient_street_and_housenumber_without_location(self):
        """Street and housenumber without city or postcode is insufficient."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1

    def test_insufficient_street_address_without_location(self):
        """Street address without city or postcode is insufficient."""
        item, pipeline, spider = get_objects(
            country="NO",
            street_address="Karl Johans gate 1",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1

    def test_insufficient_addr_full_without_location(self):
        """Full address without city or postcode is insufficient."""
        item, pipeline, spider = get_objects(
            country="NO",
            addr_full="Karl Johans gate 1",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/insufficient_input") == 1


class TestSuccessfulGeocoding:
    """Tests for successful geocoding scenarios."""

    def test_geocode_with_street_housenumber_postcode(self):
        """Geocoding with street, housenumber, and postcode."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            postcode="0154",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["adressenavn"] == "Karl Johans gate"
        assert call_params["nummer"] == "1"
        assert call_params["postnummer"] == "0154"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)
        assert result["extras"]["@geocoded"] == "geonorge"
        assert get_stat(spider, "atp/geocode/norway/success") == 1

    def test_geocode_with_street_housenumber_city(self):
        """Geocoding with street, housenumber, and city."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            city="Oslo",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["adressenavn"] == "Karl Johans gate"
        assert call_params["nummer"] == "1"
        assert call_params["poststed"] == "Oslo"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)
        assert result["extras"]["@geocoded"] == "geonorge"

    def test_geocode_with_street_address_and_postcode(self):
        """Geocoding with street_address and postcode."""
        item, pipeline, spider = get_objects(
            country="NO",
            street_address="Karl Johans gate 1",
            postcode="0154",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["adressetekst"] == "Karl Johans gate 1"
        assert call_params["postnummer"] == "0154"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)

    def test_geocode_with_street_address_and_city(self):
        """Geocoding with street_address and city."""
        item, pipeline, spider = get_objects(
            country="NO",
            street_address="Karl Johans gate 1",
            city="Oslo",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["adressetekst"] == "Karl Johans gate 1"
        assert call_params["poststed"] == "Oslo"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)

    def test_geocode_with_addr_full_and_postcode(self):
        """Geocoding with addr_full and postcode (fuzzy search)."""
        item, pipeline, spider = get_objects(
            country="NO",
            addr_full="Karl Johans gate 1, 0154 Oslo",
            postcode="0154",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["sok"] == "Karl Johans gate 1, 0154 Oslo"
        assert call_params["postnummer"] == "0154"
        assert call_params["fuzzy"] == "true"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)

    def test_geocode_with_addr_full_and_city(self):
        """Geocoding with addr_full and city (fuzzy search)."""
        item, pipeline, spider = get_objects(
            country="NO",
            addr_full="Karl Johans gate 1, Oslo",
            city="Oslo",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["sok"] == "Karl Johans gate 1, Oslo"
        assert call_params["poststed"] == "Oslo"
        assert call_params["fuzzy"] == "true"

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)

    def test_geocode_priority_specific_address_over_full(self):
        """More specific address fields should be used before addr_full."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            postcode="0154",
            addr_full="Some other address",  # Should be ignored
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(59.9139, 10.7522)
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        # Should use specific fields, not addr_full
        assert call_params["adressenavn"] == "Karl Johans gate"
        assert call_params["nummer"] == "1"
        assert "sok" not in call_params


class TestApiParameters:
    """Tests for API parameters construction."""

    def test_api_parameters_coordinate_system(self):
        """Verify correct coordinate system is requested."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["utkoordsys"] == 4258  # WGS84

    def test_api_parameters_single_result(self):
        """Verify only one result is requested."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["treffPerSide"] == 1

    def test_api_parameters_minimal_response(self):
        """Verify minimal response fields are requested."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["filtrer"] == "adresser.representasjonspunkt"


class TestNoResults:
    """Tests for when geocoding returns no results."""

    def test_no_addresses_in_response(self):
        """Handle response with empty addresses list."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Nonexistent Street",
            housenumber="999",
            postcode="0000",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert "@geocoded" not in result.get("extras", {})
        assert get_stat(spider, "atp/geocode/norway/no_result") == 1

    def test_missing_representasjonspunkt(self):
        """Handle response where address lacks coordinates."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"name": "Some address"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/no_result") == 1

    def test_missing_lat_in_coordinates(self):
        """Handle response where lat is missing."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"representasjonspunkt": {"lon": 10.7522}}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/no_result") == 1

    def test_missing_lon_in_coordinates(self):
        """Handle response where lon is missing."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"representasjonspunkt": {"lat": 59.9139}}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/no_result") == 1


class TestApiErrors:
    """Tests for API error handling."""

    def test_timeout_error(self):
        """Handle API timeout."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        with patch.object(pipeline.session, "get", side_effect=requests.Timeout("Timeout")):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/timeout") == 1

    def test_connection_error(self):
        """Handle connection error."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        with patch.object(pipeline.session, "get", side_effect=requests.ConnectionError("Connection failed")):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/api_error") == 1

    def test_http_error(self):
        """Handle HTTP error response."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/api_error") == 1

    def test_json_parse_error(self):
        """Handle invalid JSON response."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/parse_error") == 1

    def test_invalid_coordinate_values(self):
        """Handle non-numeric coordinate values in response."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"adresser": [{"representasjonspunkt": {"lat": "invalid", "lon": "invalid"}}]}

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert get_lat_lon(result) is None
        assert get_stat(spider, "atp/geocode/norway/no_result") == 1


class TestCoordinateConversion:
    """Tests for coordinate type handling."""

    def test_string_coordinates(self):
        """Handle coordinates returned as strings."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"adresser": [{"representasjonspunkt": {"lat": "59.9139", "lon": "10.7522"}}]}

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        coords = get_lat_lon(result)
        assert coords == (59.9139, 10.7522)

    def test_integer_coordinates(self):
        """Handle coordinates returned as integers."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"adresser": [{"representasjonspunkt": {"lat": 60, "lon": 10}}]}

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        coords = get_lat_lon(result)
        assert coords == (60.0, 10.0)


class TestBothCityAndPostcode:
    """Tests when both city and postcode are provided."""

    def test_with_street_housenumber_city_and_postcode(self):
        """Both city and postcode are passed to API."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            city="Oslo",
            postcode="0154",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["poststed"] == "Oslo"
        assert call_params["postnummer"] == "0154"


class TestItemIntegrity:
    """Tests to ensure original item data is preserved."""

    def test_original_address_fields_preserved(self):
        """Original address fields should not be modified."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            city="Oslo",
            postcode="0154",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") == "Karl Johans gate"
        assert result.get("housenumber") == "1"
        assert result.get("city") == "Oslo"
        assert result.get("postcode") == "0154"
        assert result.get("country") == "NO"

    def test_existing_extras_preserved(self):
        """Existing extras should be preserved when adding geocoded marker."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Karl Johans gate",
            housenumber="1",
            postcode="0154",
        )
        item["extras"]["custom_field"] = "custom_value"

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result["extras"]["custom_field"] == "custom_value"
        assert result["extras"]["@geocoded"] == "geonorge"

    def test_item_returned_on_failure(self):
        """Item should always be returned even when geocoding fails."""
        item, pipeline, spider = get_objects(
            country="NO",
            street="Testveien",
            housenumber="1",
            postcode="0101",
        )

        with patch.object(pipeline.session, "get", side_effect=requests.Timeout()):
            result = pipeline.process_item(item, spider)

        # Same item should be returned
        assert result is item
        assert result.get("country") == "NO"
        assert result.get("street") == "Testveien"
