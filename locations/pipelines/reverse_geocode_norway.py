import logging

import requests

from locations.items import Feature, get_lat_lon

logger = logging.getLogger(__name__)

GEONORGE_API_URL = "https://ws.geonorge.no/adresser/v1/punktsok"


class ReverseGeocodeNorwayPipeline:
    """
    Pipeline to reverse geocode Norwegian locations that have geometry but are missing address information.

    Uses the Kartverket (Norwegian Mapping Authority) open address API.
    API docs: https://ws.geonorge.no/adresser/v1/#/

    This pipeline only processes items where:
    - The country is Norway (NO)
    - The item has valid geometry (lat/lon)
    - The item is missing address information (street_address, street, postcode, city)
    """

    def __init__(self):
        self.session = requests.Session()

    def process_item(self, item: Feature, spider) -> Feature:
        # Only process Norwegian addresses
        if item.get("country") != "NO":
            return item

        # Skip if we don't have valid geometry
        coords = get_lat_lon(item)
        if coords is None:
            return item

        # Skip if we already have sufficient address information
        if self._has_address_info(item):
            return item

        # Try to reverse geocode the coordinates
        lat, lon = coords
        address = self._reverse_geocode(lat, lon, spider)
        if address:
            self._apply_address(item, address)
            item["extras"]["@reverse_geocoded"] = "geonorge"
            spider.crawler.stats.inc_value("atp/reverse_geocode/norway/success")
            logger.debug(f"Reverse geocoded Norwegian coordinates: ({lat}, {lon})")
        else:
            spider.crawler.stats.inc_value("atp/reverse_geocode/norway/no_result")

        return item

    def _has_address_info(self, item: Feature) -> bool:
        """
        Check if the item already has sufficient address information.

        Returns True if any of the main address fields are populated.
        """
        return any(item.get(field) for field in ("street_address", "street", "postcode", "city", "addr_full"))

    def _reverse_geocode(self, lat: float, lon: float, spider) -> dict | None:
        """
        Attempt to reverse geocode coordinates using the Geonorge API.

        Returns address data dict or None if reverse geocoding fails.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "radius": 5,  # Search within 5 meters
            "koordsys": 4258,  # WGS84 input coordinate system
            "treffPerSide": 1,  # We only need the closest match
        }

        try:
            response = self.session.get(
                GEONORGE_API_URL,
                params=params,
                timeout=3,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            return self._extract_address(data)
        except requests.Timeout:
            logger.warning("Geonorge API request timed out")
            spider.crawler.stats.inc_value("atp/reverse_geocode/norway/timeout")
            return None
        except requests.RequestException as e:
            logger.warning(f"Geonorge API request failed: {e}")
            spider.crawler.stats.inc_value("atp/reverse_geocode/norway/api_error")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Geonorge API response: {e}")
            spider.crawler.stats.inc_value("atp/reverse_geocode/norway/parse_error")
            return None

    def _extract_address(self, data: dict) -> dict | None:
        """
        Extract address information from Geonorge API response.

        Returns a dict with address fields or None if no valid result found.
        """
        addresses = data.get("adresser", [])
        if not addresses:
            return None

        # Take the first (closest) match
        address = addresses[0]

        result = {}

        # Extract street name
        if adressenavn := address.get("adressenavn"):
            result["street"] = adressenavn

        # Extract house number (with optional letter)
        nummer = address.get("nummer")
        bokstav = address.get("bokstav")
        if nummer is not None:
            housenumber = str(nummer)
            if bokstav:
                housenumber += bokstav
            result["housenumber"] = housenumber

        # Extract postcode
        if postnummer := address.get("postnummer"):
            result["postcode"] = postnummer

        # Extract city (poststed)
        if poststed := address.get("poststed"):
            result["city"] = poststed

        # Extract full street address text if available
        if adressetekst := address.get("adressetekstutenadressetilleggsnavn"):
            result["street_address"] = adressetekst
        elif adressetekst := address.get("adressetekst"):
            result["street_address"] = adressetekst

        return result if result else None

    def _apply_address(self, item: Feature, address: dict) -> None:
        """
        Apply address fields to the item, only setting fields that are not already populated.
        """
        for field, value in address.items():
            if not item.get(field):
                item[field] = value
