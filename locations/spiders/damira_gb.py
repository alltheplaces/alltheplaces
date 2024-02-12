from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature


class DamiraGBSpider(Spider):
    name = "damira_gb"
    item_attributes = {"brand": "Damira", "brand_wikidata": "Q117210318"}
    start_urls = ["https://damiradental.co.uk/find-your-nearest-practice/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="col-12 | location"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3/text()").get()
            item["image"] = location.xpath(".//img/@src").get()
            item["postcode"] = location.xpath("@data-post-code").get()
            item["ref"] = item["website"] = location.xpath(
                './/a[contains(@href, "damiradental.co.uk/location/")]/@href'
            ).get()
            extract_google_position(item, location)
            yield item
