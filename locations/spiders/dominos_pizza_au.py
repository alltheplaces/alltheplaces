from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaAUSpider(CrawlSpider):
    name = "dominos_pizza_au"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.com.au/store-finder/"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores//?[-\w]+/?$")),
        Rule(LinkExtractor(allow=r"/store//?[-\w]+-\d+$"), callback="parse"),
    ]
    user_agent = BROWSER_DEFAULT
    download_timeout = 180

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "ref": response.url.split("-")[-1],
            "branch": response.xpath('//div[@class="storetitle"]/text()').get().removeprefix("Domino's "),
            "addr_full": merge_address_lines(
                filter(None, map(str.strip, response.xpath('//a[@id="open-map-address"]/text()').getall()))
            ),
            "lat": float(response.xpath('//input[@id="store-lat"]/@value').get()),
            "lon": float(response.xpath('//input[@id="store-lon"]/@value').get()),
            "phone": response.xpath('//div[@id="store-tel"]/a/@href').get("").replace("tel:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        hours_text = " ".join(
            filter(
                None,
                map(str.strip, response.xpath('//span[@class="trading-day" or @class="trading-hour"]/text()').getall()),
            )
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)

        yield Feature(**properties)
