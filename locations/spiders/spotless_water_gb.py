import json
import re
from typing import Any

from parsel import Selector
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Vending, add_vending, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.extract_gb_postcode import GB_POSTCODE_PATTERN


class SpotlessWaterGBSpider(Spider):
    name = "spotless_water_gb"
    item_attributes = {"brand": "SpotlessWater"}
    start_urls = ["https://www.spotlesswater.co.uk/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r";[\n\s]+var locations = (\[.+\]);", response.text).group(1)):
            item = Feature()
            if postcode := GB_POSTCODE_PATTERN.search(location["title"].upper()):
                item["postcode"] = postcode.group(1)
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            sel = Selector(location["content"])
            item["image"] = sel.xpath(
                "//img[not(@src='https://spotless.blob.core.windows.net/profilepicture/')]/@src"
            ).get()
            item["addr_full"] = sel.xpath("//p/text()").get()
            item["website"] = sel.xpath("//a[contains(@href, 'spotlesswater')]/@href").get()
            item["ref"] = item["website"] or item["lat"]

            apply_category(Categories.VENDING_MACHINE, item)
            add_vending(Vending.WATER, item)
            apply_yes_no("distilled_water", item, True)
            apply_yes_no("reusable_packaging:accept=only", item, True)
            apply_yes_no("drinking_water", item, False, True)

            yield item
