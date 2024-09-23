from typing import Any
import json

from scrapy.http import HtmlResponse
from scrapy.spiders import Spider
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from urllib.parse import urljoin
from scrapy.http import Response

class SweatyBettySpider(Spider):
    name = "Sweaty Betty"
    item_attributes = {"brand": "Sweaty Betty", "brand_wikidata": "Q7654224"}
    start_urls = ["https://www.sweatybetty.com/shop-finder"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        content = response.xpath('//script[@id="mobify-data"]/text()').get()
        data = json.loads(content)
        for area in data["__PRELOADED_STATE__"]["pageProps"]["allShops"]:
          for location in area["stores"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            s=location["name"]
            slug="".join(s.split()).lower() + "-" + location["storeId"]
            item["website"] = urljoin("https://www.sweatybetty.com/shop-details/", slug)
            #if location.get("storeHours"):
            #   item["opening_hours"] = OpeningHours()
            #     xpath("./@data-day").get()+ " "
            #    xpath("./@data-open").get()+ "-"
            #    xpath("./@data-close").get()
            yield item
