from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LiquorMartCASpider(Spider):
    """Spider for Liquor Mart and Liquor Mart Express stores (Manitoba, Canada).
    Closes #7007
    """

    name = "liquor_mart_ca"
    item_attributes = {"brand": "Liquor Mart", "brand_wikidata": "Q124030913"}
    start_urls = ["https://www.liquormarts.ca/liquormarts"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.css("div.geolocation-location[data-lat]"):
            item = Feature()
            item["ref"] = location.attrib.get("id")
            item["lat"] = location.attrib.get("data-lat")
            item["lon"] = location.attrib.get("data-lng")

            name = location.css("div.views-field-field-store-name .field-content::text").get("").strip()
            if "Express" in name:
                item["brand"] = "Liquor Mart Express"
                item["brand_wikidata"] = "Q124030913"
            item["branch"] = name.removeprefix("Liquor Mart Express").removeprefix("Liquor Mart").strip() or None

            item["street_address"] = (
                location.css("div.views-field-field-location-address-line1 .field-content::text").get("").strip()
                or None
            )
            item["city"] = (
                location.css("div.views-field-field-location-locality .field-content::text").get("").strip() or None
            )
            item["postcode"] = (
                location.css("div.views-field-field-location-postal-code .field-content::text").get("").strip() or None
            )
            item["country"] = "CA"
            item["state"] = "MB"

            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
