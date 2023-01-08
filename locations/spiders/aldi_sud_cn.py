from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AldiSudCNSpider(Spider):
    name = "aldi_sud_cn"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "CN"}
    start_urls = ["https://www.aldi.cn/images/2019aldi/assets/js/stores.json"]

    def parse(self, response, **kwargs):
        districts = response.json().values()
        for district in districts:
            for id, store in district["stores"].items():
                item = Feature()
                item["ref"] = id

                item["name"] = store["title-en"]
                item["addr_full"] = store["address-en"]

                oh = OpeningHours()
                for day in DAYS:
                    start_time, end_time = store["hours"].split("-")
                    oh.add_range(day, start_time, end_time)
                item["opening_hours"] = oh.as_opening_hours()

                # TODO: Transform store["locationX"] store["locationX"]

                item["extras"] = {"map": store["mapLink"]}

                yield item
