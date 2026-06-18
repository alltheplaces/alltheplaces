import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SokolCZSpider(Spider):
    name = "sokol_cz"
    item_attributes = {
        "brand": "Sokol",
        "brand_wikidata": "Q954854",
        "country": "CZ",
    }
    # We make two sequential POST requests to the same endpoint:
    # one for marker coordinates and one for info-window content (address + slug).
    start_urls = ["https://sokol.eu/pobocky/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable:
        # Fetch map markers (name, lat, lng) and info pins (address HTML) in one go.
        yield FormRequest(
            url="https://sokol.eu/ajax.php",
            formdata={"action": "markers", "type": "map"},
            headers={"Referer": "https://sokol.eu/pobocky/"},
            callback=self.parse_markers,
        )

    def parse_markers(self, response: Response, **kwargs: Any) -> Iterable:
        markers = response.json()
        yield FormRequest(
            url="https://sokol.eu/ajax.php",
            formdata={"action": "pins", "type": "map"},
            headers={"Referer": "https://sokol.eu/pobocky/"},
            callback=self.parse_pins,
            cb_kwargs={"markers": markers},
        )

    def parse_pins(self, response: Response, markers: list, **kwargs: Any) -> Iterable:
        pins = response.json()
        for marker, pin in zip(markers, pins):
            name_raw, lat, lng = marker
            html = pin[0] if isinstance(pin, list) else pin

            name = name_raw.strip()

            # Extract slug used as stable ref (e.g. "tj-sokol-frydlant-nad-ostravici")
            slug_match = re.search(r'href="/sokolovna/([^"]+)"', html)
            slug = slug_match.group(1) if slug_match else name

            # Address paragraphs: skip the "Adresa:" label
            addr_parts = [
                p.strip() for p in re.findall(r"<p>([^<]+)</p>", html) if p.strip() and p.strip() != "Adresa:"
            ]
            street = addr_parts[0] if len(addr_parts) > 0 else None
            city = addr_parts[1] if len(addr_parts) > 1 else None

            item = Feature()
            item["ref"] = slug
            item["name"] = name
            item["lat"] = float(lat)
            item["lon"] = float(lng)
            item["street_address"] = street
            item["city"] = city
            item["website"] = f"https://sokol.eu/sokolovna/{slug}"

            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            yield item
