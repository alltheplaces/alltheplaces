import logging

import requests

from locations.items import Feature, get_lat_lon, set_lat_lon

logger = logging.getLogger(__name__)

GEONORGE_API_URL = "https://ws.geonorge.no/adresser/v1/sok"


class GeocodeNorwayPipeline:
    """
    Pipeline to geocode Norwegian addresses that are missing geometry.

    Uses the Kartverket (Norwegian Mapping Authority) open address API.
    API docs: https://ws.geonorge.no/adresser/v1/#/

    This pipeline only processes items where:
    - The country is Norway (NO)
    - The item does not have valid geometry
    - The item has enough address information to attempt geocoding
    """

    def __init__(self):
        self.session = requests.Session()

    def process_item(self, item: Feature, spider) -> Feature:
        # Only process Norwegian addresses
        if item.get("country") != "NO":
            return item

        # Skip if we already have valid geometry
        if get_lat_lon(item) is not None:
            return item

        # Try to geocode the address
        coords = self._geocode_address(item, spider)
        if coords:
            lat, lon = coords
            set_lat_lon(item, lat, lon)
            item["extras"]["@geocoded"] = "geonorge"
            spider.crawler.stats.inc_value("atp/geocode/norway/success")
            logger.debug(f"Geocoded Norwegian address: ({lat}, {lon})")
        else:
            spider.crawler.stats.inc_value("atp/geocode/norway/no_result")

        return item

    def _geocode_address(self, item: Feature, spider) -> tuple[float, float] | None:
        """
        Attempt to geocode an address using the Geonorge API.

        Returns a tuple of (lat, lon) or None if geocoding fails.
        """
        # Build search query from available address components
        search_params = self._build_search_params(item)

        if not search_params:
            spider.crawler.stats.inc_value("atp/geocode/norway/insufficient_input")
            return None

        try:
            response = self.session.get(
                GEONORGE_API_URL,
                params=search_params,
                timeout=3,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            return self._extract_coordinates(data)
        except requests.Timeout:
            logger.warning("Geonorge API request timed out")
            spider.crawler.stats.inc_value("atp/geocode/norway/timeout")
            return None
        except requests.RequestException as e:
            logger.warning(f"Geonorge API request failed: {e}")
            spider.crawler.stats.inc_value("atp/geocode/norway/api_error")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Geonorge API response: {e}")
            spider.crawler.stats.inc_value("atp/geocode/norway/parse_error")
            return None

    def _build_search_params(self, item: Feature) -> dict | None:
        """
        Build search parameters for the Geonorge API from item address fields.

        Returns None if insufficient address data is available.
        """
        params = {
            "utkoordsys": 4258,  # WGS84 coordinate system (compatible with GeoJSON)
            "treffPerSide": 1,  # We only need the best match
            "filtrer": "adresser.representasjonspunkt",  # Only return coordinates to reduce response size
        }

        if houseNumber := item.get("housenumber"):
            params["nummer"] = houseNumber

        if city := item.get("city"):
            params["poststed"] = city

        if postalCode := item.get("postcode"):
            params["postnummer"] = postalCode

        if street := item.get("street"):
            params["adressenavn"] = street

        # If we have postnummer or poststed and adressenavn and nummer, we can attempt geocoding
        if "adressenavn" in params and "nummer" in params and ("postnummer" in params or "poststed" in params):
            return params

        if streetAddr := item.get("street_address"):
            params["adressetekst"] = streetAddr

        # If we have postnummer or poststed and adressetekst, we can attempt geocoding
        if "adressetekst" in params and ("postnummer" in params or "poststed" in params):
            return params

        if fullAddr := item.get("addr_full"):
            params["sok"] = fullAddr

        # If we have postnummer or poststed and full address, we can attempt fuzzy geocoding
        if "sok" in params and ("postnummer" in params or "poststed" in params):
            params["fuzzy"] = "true"
            return params

        # Not enough address data to attempt geocoding
        return None

    def _extract_coordinates(self, data: dict) -> tuple[float, float] | None:
        """
        Extract coordinates from Geonorge API response.

        Returns a tuple of (lat, lon) or None if no valid result found.
        """
        addresses = data.get("adresser", [])
        if not addresses:
            return None

        # Take the first (best) match
        address = addresses[0]
        point = address.get("representasjonspunkt")
        if not point:
            return None

        lat = point.get("lat")
        lon = point.get("lon")

        if lat is not None and lon is not None:
            try:
                return (float(lat), float(lon))
            except (ValueError, TypeError):
                return None

        return None
