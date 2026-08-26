from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RemaxGBSpider(Spider):
    name = "remax_gb"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    start_urls = ["https://remax.co.uk/re-max-offices/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@id="resultscontainer"]//*[@class="pf-itemcontainer"]'):
            item = Feature()
            item["name"] = location.xpath('.//*[@class="officename"]/text()').get()
            item["street_address"] = location.xpath('.//*[@class="profileaddrdetails"]/text()').get()
            item["addr_full"] = merge_address_lines(
                location.xpath('.//*[@class="profileaddrdetails"]//text()').getall()
            )
            item["website"] = item["ref"] = response.urljoin(location.xpath(".//a/@href").get())
            yield item
