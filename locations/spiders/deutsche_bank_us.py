from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class DeutscheBankUSSpider(Spider):
    name = "deutsche_bank_us"
    item_attributes = {"brand": "Deutsche Bank", "brand_wikidata": "Q66048"}
    start_urls = ["https://country.db.com/usa/contact"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.xpath(r"//tbody/tr")
        locations.pop(0)
        state = ""
        for poi in locations:
            if s := poi.xpath("./td[1]/text()").get():
                state = s
            item = Feature()
            item["street_address"] = poi.xpath("./td[2]/text()").get()
            item["city"] = poi.xpath("./td[3]/text()").get()
            item["postcode"] = poi.xpath("./td[4]/text()").get()
            item["state"] = state
            apply_category(Categories.BANK, item)

            yield item
