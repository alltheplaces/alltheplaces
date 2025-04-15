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
                for ref, store in store_data["stores"].items():
                    item = Feature()
                    item["ref"] = ref
                    item["branch"] = store["title-en"].removeprefix("ALDI ").removesuffix(" Store")
                    item["addr_full"] = store["address-en"]

                    try:
                        oh = OpeningHours()
                        start_time, end_time = store["hours"].split("-")
                        oh.add_days_range(DAYS, start_time, end_time)
                        item["opening_hours"] = oh
                    except:
                        self.logger.error("Error parsing opening hours: {}".format(store["hours"]))

                    # TODO: Transform store["locationX"] store["locationX"]

                    item["extras"] = {"map": store["mapLink"]}

                    apply_category(Categories.SHOP_SUPERMARKET, item)

                    yield item
