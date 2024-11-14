from datetime import datetime
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.aw_restaurants import AwRestaurantsSpider
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.spiders.ljsilvers import LjsilversSpider
from locations.spiders.taco_bell import TACO_BELL_SHARED_ATTRIBUTES

brands_map = {
    "KA": [KFC_SHARED_ATTRIBUTES, AwRestaurantsSpider.item_attributes],
    "KB": [KFC_SHARED_ATTRIBUTES, TACO_BELL_SHARED_ATTRIBUTES],
    "KFC": [KFC_SHARED_ATTRIBUTES],
    "KL": [KFC_SHARED_ATTRIBUTES, LjsilversSpider.item_attributes],
}


class KbpFoodsSpider(Spider):
    name = "kbp_foods"
    start_urls = ["https://kbp-foods.com/wp-admin/admin-ajax.php?action=get_all_locations"]
    item_attributes = {"operator": "KBP Foods"}
    brands = {}
    start_dates = {}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            self.brands[location["title"]] = location["brand"]
            self.start_dates[location["title"]] = datetime.strptime(location["date_opened"], "%m/%d/%Y").strftime(
                "%Y-%m-%d"
            )

            yield self.make_request(1)

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://kbp-foods.com/wp-json/facetwp/v1/refresh",
            data={
                "action": "facetwp_refresh",
                "data": {"facets": {"proximity": [], "map": []}, "template": "locations", "paged": page},
            },
            cb_kwargs={"page": page},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        if data := response.json()["settings"]["map"]["locations"]:
            for store in data:
                item = Feature()
                html_data = Selector(text=store["content"])
                item["ref"] = html_data.xpath("//h2/text()").get()
                item["lat"] = store["position"]["lat"]
                item["lon"] = store["position"]["lng"]
                item["addr_full"] = html_data.xpath('//*[@class="fwpl-item"]/text()').get()
                item["phone"] = html_data.xpath('//*[contains(@href, "tel:")]/text()').get()

                item["extras"]["start_date"] = self.start_dates[item["ref"]]

                apply_category(Categories.FAST_FOOD, item)

                if brands := brands_map.get(self.brands[item["ref"]]):
                    for b in brands:
                        i = item.deepcopy()
                        i["ref"] = "{}-{}".format(item["ref"], b["brand"])
                        i.update(b)
                        yield i
                else:
                    self.logger.error("Unmapped brand: {}".format(self.brands[item["ref"]]))
                    yield item

            yield self.make_request(kwargs["page"] + 1)
