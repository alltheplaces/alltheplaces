import hashlib
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature

# The store list is plain static HTML (no storefinder plugin, no JSON-LD).
# Each store is a "<strong>street</strong> | CITY, POSTCODE | PHONE | <a
# href="https://goo.gl/maps/...">Cómo llegar</a>" line grouped under an
# <h3> province heading. The "Cómo llegar" links are Google Maps
# place/search links (geocoded from the address, sometimes via a goo.gl
# short link), not embeds with a site-published pin, so no coordinates are
# extracted here.
ADDRESS_RE = re.compile(r"^(.*?),?\s*(\d{5})$")


class PanishopESSpider(Spider):
    name = "panishop_es"
    item_attributes = {
        "brand": "Panishop",
        "brand_wikidata": "Q108472015",
        "name": "Panishop",
    }
    start_urls = ["https://panishop.com/tiendas-3/"]

    def parse(self, response):
        for el in response.css(".page_container_inner h3, .page_container_inner p"):
            if el.root.tag != "p":
                continue
            street = el.css("strong::text").get()
            if not street:
                continue
            street = street.strip()
            full_text = " ".join(t.strip() for t in el.css("::text").getall() if t.strip())
            parts = [p.strip() for p in full_text.split("|")]
            if len(parts) < 3:
                continue
            city_postcode, phone = parts[1], parts[2]
            if m := ADDRESS_RE.match(city_postcode):
                city, postcode = m.group(1).strip(), m.group(2)
            else:
                city, postcode = city_postcode, None

            item = Feature()
            item["ref"] = hashlib.sha1(f"{street}|{city_postcode}".encode("utf-8")).hexdigest()
            item["street_address"] = street
            item["city"] = city
            item["postcode"] = postcode
            item["country"] = "ES"
            item["phone"] = phone
            apply_category(Categories.SHOP_BAKERY, item)
            yield item
