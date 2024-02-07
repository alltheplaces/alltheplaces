from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TommyHRSpider(Spider):
    # "businessHours" in the next data show incorrect opening hours for Sundays
    name = "tommy_hr"
    item_attributes = {"brand": "Tommy", "brand_wikidata": "Q12643718"}
    start_urls = ["https://www.tommy.hr/_next/data/NQBnI1_5yBtg95innap3m/hr-HR/prodavaonice.json"]

    def parse(self, response: Response):
        for store in response.json()["pageProps"]["dehydratedState"]["queries"][1]["state"]["data"]["hydra:member"]:
            store["address"]["street_address"] = store["address"].pop("street")
            item = DictParser.parse(store)
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
