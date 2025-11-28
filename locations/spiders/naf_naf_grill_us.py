from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class NafNafGrillUSSpider(Spider):
    name = "naf_naf_grill_us"
    item_attributes = {"brand_wikidata": "Q111901442"}
    start_urls = ["https://www.nafnafgrill.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//h3[contains(text(), "Naf Naf Grill")]/..'):
            item = Feature()
            item["branch"] = location.xpath("h3/text()").get().removeprefix("Naf Naf Grill ")
            item["ref"] = location.xpath("h3/@id").get()
            item["addr_full"] = location.xpath("p/text()").get()

            item["website"] = "https://www.nafnafgrill.com/locations/#{}".format(item["ref"])

            yield item
