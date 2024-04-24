from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class BPPulseGBSpider(Spider):
    name = "bp_pulse_gb"
    item_attributes = {"brand_wikidata": "Q39057719"}

    @staticmethod
    def make_request(page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://chargevision4.com/api/polar-plus/posts?page={page}",
            headers={"API_KEY": "6147-f93fad682f5a-2a927fe95546-2d31"},
            meta={"page": page},
        )

    def start_requests(self):
        yield self.make_request(1)

    def parse(self, response, **kwargs):
        for ref, location in response.json()["data"].items():
            item = Feature()

            item["lat"] = location[0]
            item["lon"] = location[1]
            item["ref"] = ref
            apply_category(Categories.CHARGING_STATION, item)
            yield item

        if response.json()["per_page"] * response.meta["page"] < response.json()["total"]:
            yield self.make_request(response.meta["page"] + 1)
