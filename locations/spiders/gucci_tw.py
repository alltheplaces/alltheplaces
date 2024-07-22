from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class GucciTWSpider(Spider):
    name = "gucci_tw"
    item_attributes = {"brand": "Gucci", "brand_wikidata": "Q178516"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        south = 21.9705713974
        west = 120.106188593
        north = 25.2954588893
        east = 121.951243931
        yield Request(
            f"https://www.gucci.com/us/en/store/all?south={south}&west={west}&north={north}&east={east}",
            headers={"Referer": "https://www.gucci.com/us/en/store"},
        )

    def parse(self, response):
        if response.json()["status"] == "200":
            for store in response.json()["features"]:
                item = DictParser.parse(store)
                item["website"] = f"""https://www.gucci.com/us/en{item["website"]}"""
                yield item
