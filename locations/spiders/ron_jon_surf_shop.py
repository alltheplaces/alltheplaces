import json

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class RonJonSurfShopSpider(PlaywrightSpider):
    name = "ron_jon_surf_shop"
    item_attributes = {"name": "Ron Jon Surf Shop", "brand": "Ron Jon Surf Shop", "brand_wikidata": "Q7363993"}
    allowed_domains = ["www.ronjonsurfshop.com"]
    start_urls = ["https://www.ronjonsurfshop.com/ajax/store-locator?searchText=&pagesize=15&pageNumber=1"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        for data in json.loads(response.xpath("//pre/text()").get())["results"]:
            item = DictParser.parse(data)
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(data["url"])

            apply_category({"shop": "surf"}, item)

            yield item
