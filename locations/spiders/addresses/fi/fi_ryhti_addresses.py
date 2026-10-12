from typing import Any, AsyncIterator, Iterable

from pyproj import Transformer
from pyproj.exceptions import ProjError
from scrapy.http import JsonRequest, Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses


class FiRyhtiAddressesSpider(AddressSpider):
    """
    Addresses from Ryhti, Finland's built environment information system.

    Source is the open_address collection of the OGC API Features service
    maintained by the Finnish Environment Institute (Syke). Address points
    are created in structured form in Ryhti; in the first phase they have
    no own location points but are linked to building objects.
    Dataset documentation:
    https://ckan.ymparisto.fi/dataset/rakennetun-ympariston-tietojarjestelman-rakennusten-osoitetiedot

    The live API returns WGS84 coordinates for f=json. The downloadable
    open_address.json dump instead stores EPSG:3067 coordinates, so
    coordinates outside valid WGS84 ranges are reprojected from EPSG:3067.
    """

    name = "fi_ryhti_addresses"
    allowed_domains = ["paikkatiedot.ymparisto.fi"]
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Contains data from Ryhti - Built Environment Information System distributed by the Finnish Environment Institute (Syke)",
        "attribution:website": "https://ckan.ymparisto.fi/dataset/rakennetun-ympariston-tietojarjestelman-rakennusten-osoitetiedot",
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 300, "ROBOTSTXT_OBEY": False}

    base_url = (
        "https://paikkatiedot.ymparisto.fi/geoserver/ryhti_building/ogc/features/v1/collections/open_address/items"
    )
    page_size = 10000

    _transformer = Transformer.from_crs(3067, 4326, always_xy=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_page_urls: set[str] = set()

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url=f"{self.base_url}?f=json&limit={self.page_size}&startIndex=0", callback=self.parse)

    def parse(self, response: Response, **kwargs) -> Iterable[Feature | JsonRequest]:
        data = response.json()  # ty: ignore[unresolved-attribute]
        for feature in data.get("features") or []:
            if item := self.parse_feature(feature):
                yield item
        for link in data.get("links") or []:
            if link.get("rel") == "next" and link.get("href"):
                next_url = response.urljoin(link["href"])
                if next_url in self._seen_page_urls:
                    # Server re-offered a page; stop instead of looping forever.
                    self._count("duplicate_next_page")
                    break
                self._seen_page_urls.add(next_url)
                yield JsonRequest(url=next_url, callback=self.parse)
                break

    def parse_feature(self, feature: dict) -> Feature | None:
        props = feature.get("properties", {}) or {}
        if not (ref := self._strip_value(props.get("address_key"))):
            self._count("missing_ref")
            return None

        lon, lat = self._parse_coords(feature.get("geometry"))
        if lon is None or lat is None:
            self._count("missing_coords")
            return None

        # Finnish is the primary language; fall back to Swedish (both official).
        street_fin = self._strip_value(props.get("address_name_fin"))
        street_swe = self._strip_value(props.get("address_name_swe"))
        if not (street := street_fin or street_swe):
            self._count("missing_street")
            return None

        city_fin = self._strip_value(props.get("postal_office_fin"))
        city_swe = self._strip_value(props.get("postal_office_swe"))
        addr_fin = self._strip_value(props.get("address_fin"))
        addr_swe = self._strip_value(props.get("address_swe"))

        item = Feature()
        item["ref"] = ref
        item["lat"] = lat
        item["lon"] = lon
        item["country"] = "FI"
        item["street"] = street
        item["housenumber"] = self._format_housenumber(props)
        item["city"] = city_fin or city_swe
        if (postcode := self._strip_value(props.get("postal_code"))) and not postcode.replace("0", "").strip():
            postcode = None  # All-zero postcodes are placeholders, not real postcodes.
        item["postcode"] = postcode
        item["addr_full"] = addr_fin or addr_swe

        if street_fin and street_swe and street_swe != street_fin:
            item["extras"]["addr:street:sv"] = street_swe
        if city_fin and city_swe and city_swe != city_fin:
            item["extras"]["addr:city:sv"] = city_swe
        if addr_fin and addr_swe and addr_swe != addr_fin:
            item["extras"]["addr:full:sv"] = addr_swe
        if municipality := self._strip_value(props.get("municipality_number")):
            item["extras"]["ref:FI:municipality"] = municipality
        if building := self._strip_value(props.get("building_key")):
            item["extras"]["ref:FI:building"] = building

        return item

    def _format_housenumber(self, props: dict) -> str | None:
        # address_number is a per-building record sequence, not the housenumber ("Muuttolinnunkuja 1" has address_number 3).
        number = self._strip_value(props.get("number_part_of_address_number"))
        if number is None or not number.replace("0", "").strip():
            return None  # "0" is a placeholder for unknown, never a real housenumber.
        # Source letters are already lowercase FI style; strip only, never fold case.
        letter = self._strip_value(props.get("subdivision_letter_of_address_number")) or ""
        housenumber = f"{number}{letter}"
        number2 = self._strip_value(props.get("number_part_of_address_number2"))
        letter2 = self._strip_value(props.get("subdivision_letter_of_address_number2")) or ""
        if number2 is not None:
            housenumber += f"-{number2}{letter2}"
        elif letter2:
            # Range end carried by letter alone (e.g. "Rinnepolku 3b-c").
            housenumber += f"-{letter2}"
        return housenumber

    def _parse_coords(self, geometry: Any) -> tuple[float | None, float | None]:
        if not isinstance(geometry, dict) or geometry.get("type") != "Point":
            return None, None
        coords = geometry.get("coordinates")
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return None, None
        try:
            x, y = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None, None
        if abs(x) > 180 or abs(y) > 90:
            # Dump stores EPSG:3067, but location_srid is 3067 even for WGS84 payloads, so sniff by magnitude.
            self._count("reprojected_epsg3067")
            try:
                x, y = self._transformer.transform(x, y)
            except ProjError:
                return None, None
        if not (-180 <= x <= 180 and -90 <= y <= 90):
            return None, None
        return x, y

    def _strip_value(self, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _count(self, key: str) -> None:
        # The offline harness instantiates the spider without a crawler.
        crawler = getattr(self, "crawler", None)
        if crawler is None:
            return
        crawler.stats.inc_value(f"{self.name}/{key}")
