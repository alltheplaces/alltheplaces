import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class HomesenseSpider(CrawlSpider):
    name = "homesense"
    item_attributes = {"brand": "HomeSense", "brand_wikidata": "Q16844433"}
    start_urls = ["https://us.homesense.com/all-stores"]
    rules = [
        Rule(
            LinkExtractor(
                allow="/store-details/",
                deny=[
                    "yonkers-ny-10710/0019",
                    "totowa-nj-07512/0043",
                    "paramus-nj-07652/0008",
                    "mohegan-lake-ny-10547/0018",
                ],
            ),
            callback="parse",
        )
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = "-".join(
            [
                response.xpath('//*[@id="store-details-hero"]//h1/text()').get(),
                response.xpath('//*[@id="store-details-hero"]//h1/text()').get(),
            ]
        )
        item["addr_full"] = response.xpath('//*[@id="store-details-amenities"]//p').xpath("normalize-space()").get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["lat"], item["lon"] = re.search(r"initMap\(([0-9-\.]+),\s*([0-9-\.]+)\);", response.text).groups()
        yield item
