import re
from typing import Any

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class RidleysFamilyMarketsUSSpider(Spider):
    name = "ridleys_family_markets_us"
    item_attributes = {"brand": "Ridley's Family Markets", "brand_wikidata": "Q7332999"}
    start_urls = ["https://shopridleys.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        nonce = response.xpath("//*[@data-imm-locations-nonce]/@data-imm-locations-nonce").get()
        yield FormRequest(
            url="https://shopridleys.com/wp-admin/admin-ajax.php",
            formdata={
                "action": "imm_sections_get_stores_ajax",
                "nonce": nonce,
                "lat": "39.5",
                "lng": "-111.5",
                "city": "",
                "count": "1000",
                "all_store": "yes",
            },
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["data"]["message"]:
            item = Feature()
            item["ref"] = location["StoreID"]
            item["branch"] = location["DisplayName"]
            item["street_address"] = location["StoreAddress"]
            item["city"] = location["StoreCity"]
            item["state"] = location["StoreState"]
            item["postcode"] = location["Zip"]
            item["phone"] = location["PhoneNo"]

            if match := re.match(r"([\d:]+[AP]M)-([\d:]+[AP]M)", location.get("Hours", "")):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, match.group(1), match.group(2), time_format="%I:%M%p")

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
