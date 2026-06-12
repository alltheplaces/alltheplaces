import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature

EFFIA = {"brand": "Effia", "brand_wikidata": "Q3045894"}


class EffiaSpider(SitemapSpider):
    name = "effia"
    sitemap_urls = ["https://www.effia.com/sitemap.xml"]
    sitemap_rules = [(r"/parking/parking-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        car_park = response.css("div.car-park")
        if not car_park:
            return

        item = Feature()
        item["ref"] = car_park.attrib.get("data-poche-id") or car_park.attrib.get("data-product-id")
        item["name"] = car_park.attrib["data-title"].strip()
        item["lat"] = car_park.attrib.get("data-lat")
        item["lon"] = car_park.attrib.get("data-lon")
        item["website"] = response.url.split("?")[0]

        if item["name"].endswith("EFFIA"):
            item["name"] = item["name"].removesuffix(" EFFIA").strip(" -–")
            item.update(EFFIA)
        # else  NAOLIB + ALFAPARK

        if raw_address := car_park.attrib.get("data-address", ""):
            parts = [p.strip() for p in raw_address.split(",")]
            if len(parts) >= 3:
                item["city"] = parts[-1].title()
                item["postcode"] = parts[-2]
                item["street_address"] = ", ".join(parts[:-2])

            # To prevent border-snapping anomaly for Hendaye
            if "Hendaye" in item.get("city", ""):
                item["country"] = "FR"

        apply_category(Categories.PARKING, item)

        yield item
