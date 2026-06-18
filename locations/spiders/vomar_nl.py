import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class VomarNLSpider(SitemapSpider):
    """Spider for Vomar supermarkets in the Netherlands.
    Closes #9086
    """

    name = "vomar_nl"
    item_attributes = {"brand": "Vomar", "brand_wikidata": "Q3202837"}
    sitemap_urls = ["https://www.vomar.nl/sitemap.xml"]
    sitemap_rules = [(r"https://www\.vomar\.nl/winkels/vomar-[^/]+\.htm$", "parse_store")]

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Store data is embedded in the window.__NUXT__ blob as alias->value pairs.
        data: dict[str, str] = {}
        for m in re.finditer(r'alias:"([^"]+)"[^}]*value:"([^"]+)"', response.text):
            data[m.group(1)] = m.group(2)

        lat = data.get("latitude")
        lon = data.get("longitude")
        if not lat or not lon:
            return

        item = Feature()
        item["ref"] = data.get("shop_nr") or response.url.split("/")[-1].replace(".htm", "")
        item["street_address"] = data.get("street_and_number")
        item["postcode"] = data.get("zipcode")
        item["city"] = data.get("city")
        item["country"] = "NL"
        item["phone"] = data.get("telephone") or None
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
