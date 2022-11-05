import re
import scrapy

from locations.linked_data_parser import LinkedDataParser


class TraderJoesSpider(scrapy.Spider):
    name = "trader_joes"
    item_attributes = {"brand": "Trader Joe's", "brand_wikidata": "Q688825"}
    allowed_domains = ["traderjoes.com"]
    start_urls = [
        "https://locations.traderjoes.com/",
    ]

    def parse(self, response):
        yield from response.follow_all(css="a.listitem")
        for script in response.xpath('//script[@type="application/ld+json"]'):
            text = script.root.text
            # json with two kinds of comments
            text = re.sub(r" +//.*", "", text)
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
            script.root.text = text
        item = LinkedDataParser.parse(response, "GroceryStore")
        if item is not None and item["ref"]:
            yield item
