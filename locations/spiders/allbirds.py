from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class AllbirdsSpider(Spider):
    name = "allbirds"
    item_attributes = {"brand": "Allbirds", "brand_wikidata": "Q30591057"}
    start_urls = ["https://www.allbirds.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "storeLocations")]/text()').re_first(r"storeLocations = (\[.+\])")
        ):
            item = Feature()
            item["branch"] = location["storeName"]
            item["ref"] = location["handle"]
            item["website"] = response.urljoin(location["handle"])
            item["phone"] = location.get("phoneNumber")
            item["addr_full"] = location.get("storeAddress")
            item["street_address"] = location["streetAddress"]
            item["city"] = location["city"]
            item["state"] = location.get("stateProvince")
            item["postcode"] = location["zipPostalCode"]
            item["country"] = location["countryRegion"]
            item["lat"] = location["geoLocation"]["lat"]
            item["lon"] = location["geoLocation"]["lon"]

            apply_category(Categories.SHOP_SHOES, item)

            yield item
