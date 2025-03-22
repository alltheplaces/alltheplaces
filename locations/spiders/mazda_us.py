import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MazdaUSSpider(scrapy.Spider):
    name = "mazda_us"
    item_attributes = {"brand": "Mazda", "brand_wikidata": "Q35996"}
    start_urls = ["https://www.mazdausa.com/handlers/dealer.ajax"]

    def parse(self, response, **kwargs):
        if dealers := response.json()["body"]["results"]:
            for dealer in dealers:
                item = DictParser.parse(dealer)

                item["website"] = dealer.get("webUrl")

                if dealer.get("serviceUrl"):
                    apply_category({"shop": "car", "service": "dealer;repair"}, item)
                else:
                    apply_category(Categories.SHOP_CAR, item)

                yield item

            current_page = kwargs.get("page", 1)

            yield JsonRequest(url=f"{self.start_urls[0]}?p={current_page + 1}", cb_kwargs=dict(page=current_page + 1))
