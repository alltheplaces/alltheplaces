from scrapy import Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class RonJonSurfShopSpider(Spider):
    name = "ron_jon_surf_shop"
    item_attributes = {
        "brand": "Ron Jon Surf Shop",
        "brand_wikidata": "Q7363993",
        "extras": {
            "shop": "surf",
        },
    }
    allowed_domains = ["www.ronjonsurfshop.com"]
    start_urls = ["https://www.ronjonsurfshop.com/ajax/store-locator?searchText=&pagesize=15&pageNumber=1"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        for data in response.json()["results"]:
            item = DictParser.parse(data)

            item["website"] = response.urljoin(data["url"])

            yield item
