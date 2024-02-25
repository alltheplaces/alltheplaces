from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.automatic_spider_generator import AutomaticSpiderGenerator


class StoremapperSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "storemapper.com"}

    key = ""
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(url=f"https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/{self.key}/stores.js")

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        # Example: https://francescas.com/store-locator
        if len(response.xpath("//script[@data-storemapper-id]/@data-storemapper-id")) > 0:
            return True

        if len(response.xpath('//script[contains(text(), "https://www.storemapper.co/js/widget-3.min.js")]')) > 0:
            return True

        if len(response.xpath('//script[contains(src(), "https://www.storemapper.co/js/widget-3.min.js")]')) > 0:
            return True

        if len(response.xpath('//div[id="storemapper")]')) > 0:
            return True

        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict:
        return {
            "key": response.xpath("//script[@data-storemapper-id]/@data-storemapper-id").get(),
        }
