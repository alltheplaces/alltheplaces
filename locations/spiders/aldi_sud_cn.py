import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AldiSudCNSpider(Spider):
    name = "aldi_sud_cn"
    item_attributes = {"brand_wikidata": "Q41171672", "country": "CN"}
    start_urls = ["https://aldi.cn/assets/json/stores.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        districts = response.json().values()
        for district in districts:
            for store_data in district["district-data"].values():
                for store in store_data["stores"].values():
                    item = Feature()
                    item["ref"] = store["mapLink"]
                    item["branch"] = store["title-en"].removeprefix("ALDI ").removesuffix(" Store")
                    item["addr_full"] = store["address-en"]
                    oh = OpeningHours()
                    for day in DAYS:
                        start_time, end_time = re.search(r"(\d+:\d+)-(\d+:\d+)", store["hours"]).groups()
                        oh.add_range(day, start_time, end_time)
                    item["opening_hours"] = oh.as_opening_hours()

                    # TODO: Transform store["locationX"] store["locationX"]

                    item["extras"] = {"map": store["mapLink"]}

                    apply_category(Categories.SHOP_SUPERMARKET, item)

                    yield item
