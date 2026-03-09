from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BeaconAndBridgeMarketUSSpider(Spider):
    name = "beacon_and_bridge_market_us"
    item_attributes = {
        "brand": "Beacon & Bridge Market",
        "brand_wikidata": "Q122209684",
    }
    start_urls = ["https://www.beaconandbridge.com/locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="dmNewParagraph"][@data-ai-tag="Section title"]'):
            location_info = location.xpath("./parent::div[@data-external-id]/following-sibling::div")
            if address := clean_address(location_info.xpath('.//a[contains(@href,"maps")]/text()').getall()):
                item = Feature()
                item["branch"] = location.xpath("./h1/span/text()").get("").split("Store")[0]
                item["addr_full"] = address
                item["phone"] = (
                    location_info.xpath('.//span[contains(text(), "PHONE:")]/text()').get("").replace("PHONE:", "")
                )
                apply_category(Categories.FUEL_STATION, item)
                yield item
