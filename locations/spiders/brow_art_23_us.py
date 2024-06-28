from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BrowArt23USSpider(Spider):
    name = "brow_art_23_us"
    item_attributes = {"brand": "Brow Art 23", "brand_wikidata": "Q115675881"}
    start_urls = [
        "https://browart23.com/wp-admin/admin-ajax.php?action=yith_sl_get_results&context=frontend&filters[radius][]=500"
    ]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["markers"]:
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["website"] = "https://browart23.com/store-locator/{}/".format(location["slug"])

            sel = Selector(text=location["pin_modal"])
            item["addr_full"] = merge_address_lines(sel.xpath('//p[@class="store-address"]/text()').getall())
            item["phone"] = sel.xpath('//li[@class="store-phone"]/a/text()').get()

            yield item
