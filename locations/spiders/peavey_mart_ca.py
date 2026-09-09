from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PeaveyMartCASpider(Spider):
    name = "peavey_mart_ca"
    item_attributes = {"brand": "Peavey Mart", "brand_wikidata": "Q7158483"}
    start_urls = ["https://peaveymart.com/pages/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="pm-card"]'):
            item = Feature()
            item["branch"] = item["ref"] = location.xpath(".//h3/text()").get()
            item["addr_full"] = merge_address_lines(location.xpath('.//*[@class="pm-meta"]/small[1]//text()').getall())
            item["phone"] = location.xpath('.//*[@class="pm-meta"]/small[2]//text()').get()
            extract_google_position(item, location)
            yield item
