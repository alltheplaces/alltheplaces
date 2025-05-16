from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AgentProvocateurSpider(Spider):
    name = "agent_provocateur"
    item_attributes = {
        "brand": "Agent Provocateur",
        "brand_wikidata": "Q392755",
    }
    start_urls = [
        "https://www.agentprovocateur.com/eu_en/api/n/find?type=store&verbosity=1&filter=%7B%22verbosity%22%3A1%2C%22id%22%3A%7B%22%24nin%22%3A%5B%5D%7D%7D"
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["catalog"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            item.pop("website")
            item["postcode"] = str(item["postcode"])
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
