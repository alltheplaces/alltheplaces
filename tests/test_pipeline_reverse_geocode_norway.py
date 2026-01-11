from unittest.mock import MagicMock, patch

from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature, get_lat_lon
from locations.pipelines.reverse_geocode_norway import ReverseGeocodeNorwayPipeline


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
        ReverseGeocodeNorwayPipeline(),
        spider,
    )


def get_stat(spider, key: str) -> int | None:
    """Helper to safely get a stat value from spider crawler stats."""
    if spider.crawler and spider.crawler.stats:
        return spider.crawler.stats.get_value(key)
    return None


def mock_geonorge_response(
    adressenavn="Karl Johans gate",
    nummer=1,
    bokstav=None,
    postnummer="0154",
    poststed="OSLO",
    adressetekst="Karl Johans gate 1",
    meterDistanseTilPunkt=25.5,
):
    """Create a mock successful Geonorge punktsok API response."""
    address = {
        "adressenavn": adressenavn,
        "nummer": nummer,
        "postnummer": postnummer,
        "poststed": poststed,
        "adressetekst": adressetekst,
        "adressetekstutenadressetilleggsnavn": adressetekst,
        "meterDistanseTilPunkt": meterDistanseTilPunkt,
        "representasjonspunkt": {"lat": 59.9139, "lon": 10.7522},
    }
    if bokstav:
        address["bokstav"] = bokstav
    return {"adresser": [address]}


class TestSkipConditions:
    """Tests for conditions where reverse geocoding should be skipped."""

    def test_skip_non_norwegian_country(self):
        """Pipeline should skip items not in Norway."""
        item, pipeline, spider = get_objects(
            country="SE",
            lat=59.9139,
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        # Should not make any API calls
        mock_get.assert_not_called()
        assert result.get("street") is None

    def test_skip_empty_country(self):
        """Pipeline should skip items without a country."""
        item, pipeline, spider = get_objects(
            country=None,
            lat=59.9139,
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("street") is None

    def test_skip_missing_coordinates(self):
        """Pipeline should skip items without lat/lon."""
        item, pipeline, spider = get_objects(
            country="NO",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("street") is None

    def test_skip_invalid_coordinates(self):
        """Pipeline should skip items with invalid coordinates."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=999,  # Invalid latitude
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("street") is None

    def test_skip_existing_street_address(self):
        """Pipeline should skip items that already have street_address."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            street_address="Existing address",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("street_address") == "Existing address"

    def test_skip_existing_street(self):
        """Pipeline should skip items that already have street."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            street="Existing street",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("street") == "Existing street"

    def test_skip_existing_postcode(self):
        """Pipeline should skip items that already have postcode."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            postcode="0154",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("postcode") == "0154"

    def test_skip_existing_city(self):
        """Pipeline should skip items that already have city."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            city="Oslo",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("city") == "Oslo"

    def test_skip_existing_addr_full(self):
        """Pipeline should skip items that already have addr_full."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
            addr_full="Full address",
        )

        with patch.object(pipeline.session, "get") as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_not_called()
        assert result.get("addr_full") == "Full address"


class TestSuccessfulReverseGeocoding:
    """Tests for successful reverse geocoding scenarios."""

    def test_reverse_geocode_with_lat_lon(self):
        """Reverse geocoding with lat/lon coordinates."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["lat"] == 59.9139
        assert call_params["lon"] == 10.7522
        assert call_params["radius"] == 5

        assert result.get("street") == "Karl Johans gate"
        assert result.get("housenumber") == "1"
        assert result.get("postcode") == "0154"
        assert result.get("city") == "OSLO"
        assert result.get("street_address") == "Karl Johans gate 1"
        assert result["extras"]["@reverse_geocoded"] == "geonorge"
        assert get_stat(spider, "atp/reverse_geocode/norway/success") == 1

    def test_reverse_geocode_with_geometry(self):
        """Reverse geocoding with Point geometry."""
        item, pipeline, spider = get_objects(
            country="NO",
            geometry={"type": "Point", "coordinates": [10.7522, 59.9139]},
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            result = pipeline.process_item(item, spider)

        mock_get.assert_called_once()
        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["lat"] == 59.9139
        assert call_params["lon"] == 10.7522

        assert result.get("street") == "Karl Johans gate"
        assert result.get("postcode") == "0154"

    def test_reverse_geocode_with_house_number_letter(self):
        """Reverse geocoding returns house number with letter."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response(
            nummer=23,
            bokstav="B",
            adressetekst="Storgata 23B",
        )
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("housenumber") == "23B"
        assert result.get("street_address") == "Storgata 23B"


class TestApiParameters:
    """Tests for API parameters construction."""

    def test_api_parameters_coordinate_system(self):
        """Verify correct coordinate system is sent."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["koordsys"] == 4258  # WGS84

    def test_api_parameters_single_result(self):
        """Verify only one result is requested."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["treffPerSide"] == 1

    def test_api_parameters_radius(self):
        """Verify search radius is set."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response) as mock_get:
            pipeline.process_item(item, spider)

        call_params = mock_get.call_args.kwargs["params"]
        assert call_params["radius"] == 5


class TestNoResults:
    """Tests for when reverse geocoding returns no results."""

    def test_no_addresses_in_response(self):
        """No results when API returns empty address list."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert result.get("postcode") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/no_result") == 1

    def test_empty_address_fields(self):
        """No results when API returns address with no useful fields."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"meterDistanseTilPunkt": 50}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/no_result") == 1


class TestApiErrors:
    """Tests for API error handling."""

    def test_timeout_error(self):
        """Timeout errors are handled gracefully."""
        import requests

        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get", side_effect=requests.Timeout()):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/timeout") == 1

    def test_connection_error(self):
        """Connection errors are handled gracefully."""
        import requests

        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get", side_effect=requests.ConnectionError()):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/api_error") == 1

    def test_http_error(self):
        """HTTP errors are handled gracefully."""
        import requests

        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/api_error") == 1

    def test_json_parse_error(self):
        """JSON parse errors are handled gracefully."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/parse_error") == 1


class TestPartialAddressData:
    """Tests for handling partial address data from API."""

    def test_only_street_returned(self):
        """Handle response with only street name."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"adressenavn": "Testveien"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") == "Testveien"
        assert result.get("housenumber") is None
        assert result.get("postcode") is None
        assert get_stat(spider, "atp/reverse_geocode/norway/success") == 1

    def test_only_postcode_returned(self):
        """Handle response with only postcode."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"postnummer": "0154", "poststed": "OSLO"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("postcode") == "0154"
        assert result.get("city") == "OSLO"
        assert result.get("street") is None

    def test_house_number_zero(self):
        """Handle house number of 0."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"adresser": [{"adressenavn": "Testveien", "nummer": 0}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street") == "Testveien"
        assert result.get("housenumber") == "0"


class TestItemIntegrity:
    """Tests to ensure original item data is preserved."""

    def test_original_coordinates_preserved(self):
        """Coordinates should not be modified."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("lat") == 59.9139
        assert result.get("lon") == 10.7522

    def test_existing_extras_preserved(self):
        """Existing extras should be preserved."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )
        item["extras"]["existing_key"] = "existing_value"

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result["extras"]["existing_key"] == "existing_value"
        assert result["extras"]["@reverse_geocoded"] == "geonorge"

    def test_item_returned_on_failure(self):
        """Item should be returned unchanged on API failure."""
        import requests

        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        with patch.object(pipeline.session, "get", side_effect=requests.Timeout()):
            result = pipeline.process_item(item, spider)

        assert result.get("lat") == 59.9139
        assert result.get("lon") == 10.7522
        assert result.get("country") == "NO"

    def test_other_fields_preserved(self):
        """Other item fields should not be affected."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )
        item["name"] = "Test Store"
        item["phone"] = "+47 12345678"
        item["ref"] = "store-001"

        mock_response = MagicMock()
        mock_response.json.return_value = mock_geonorge_response()
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("name") == "Test Store"
        assert result.get("phone") == "+47 12345678"
        assert result.get("ref") == "store-001"


class TestFallbackToAdressetekst:
    """Tests for fallback behavior when adressetekstutenadressetilleggsnavn is not available."""

    def test_uses_adressetekst_when_no_adressetekstutenadressetilleggsnavn(self):
        """Falls back to adressetekst when adressetekstutenadressetilleggsnavn is not available."""
        item, pipeline, spider = get_objects(
            country="NO",
            lat=59.9139,
            lon=10.7522,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "adresser": [
                {
                    "adressenavn": "Karl Johans gate",
                    "nummer": 1,
                    "adressetekst": "Slottet, Karl Johans gate 1",  # Includes tilleggsnavn
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(pipeline.session, "get", return_value=mock_response):
            result = pipeline.process_item(item, spider)

        assert result.get("street_address") == "Slottet, Karl Johans gate 1"
