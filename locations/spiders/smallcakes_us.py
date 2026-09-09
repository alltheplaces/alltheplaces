import re
from hashlib import sha1
from html import unescape

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# Each store's marker (name, address, phone, website) and coordinates are
# embedded directly in the page's inline JavaScript as plain-text pairs, so
# no browser rendering is needed to read them.
LOCATION_RE = re.compile(
    r'popUpContent = "<p>(?P<popup>.*?)</p>"\s*' r"var marker = L\.marker\(\[(?P<lat>-?[\d.]+),\s*(?P<lon>-?[\d.]+)\]",
)


class SmallcakesUSSpider(Spider):
    name = "smallcakes_us"
    item_attributes = {"brand": "Smallcakes", "brand_wikidata": "Q62384749", "name": "Smallcakes"}
    start_urls = ["https://www.smallcakescupcakery.com/locations/"]

    def parse(self, response: Response):
        for match in LOCATION_RE.finditer(response.text):
            parts = match.group("popup").split("<br>")
            if len(parts) != 4:
                continue

            name, address, phone, website_html = (p.strip() for p in parts)

            if "coming soon" in name.lower():
                # Not yet open, so there is nothing to map.
                continue

            website_match = re.search(r"href='([^']*)'", website_html)
            website = website_match.group(1) if website_match else None

            # Address is "street[, street2], city, state, zip".
            street_address, city, state, postcode = (p.strip() for p in address.rsplit(",", 3))

            item = Feature()
            item["ref"] = sha1(f"{address}|{match.group('lat')}|{match.group('lon')}".encode("utf-8")).hexdigest()
            item["branch"] = unescape(name)
            item["street_address"] = street_address
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            item["country"] = "US"
            item["phone"] = phone or None
            item["website"] = unescape(website) if website else None
            item["lat"] = match.group("lat")
            item["lon"] = match.group("lon")

            apply_category(Categories.SHOP_PASTRY, item)

            yield item
