from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PepeJeansSpider(Spider):
    name = "pepe_jeans"
    item_attributes = {"brand": "Pepe Jeans", "brand_wikidata": "Q426992"}
    start_urls = ["https://www.pepejeans.com/intl/en/page/store-locator.html"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="store-card"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h2/text()").get().removeprefix("Pepe Jeans ")
            item["street_address"] = location.xpath(".//p/text()").get()
            item["addr_full"] = item["ref"] = merge_address_lines(
                [item["street_address"], location.xpath(".//p[2]/text()").get()]
            )
            item["phone"] = location.xpath('.//*[@class = "phone"]/text()').get()
            extract_google_position(item, location)
            yield item
