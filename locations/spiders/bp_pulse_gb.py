from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature


class BPPulseGBSpider(Spider):
    name = "bp_pulse_gb"
    item_attributes = {"brand": "bp pulse", "brand_wikidata": "Q39057719", "country": "GB"}

    @staticmethod
    def make_request(page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://chargevision4.com/api/polar-plus/posts?page={page}",
            headers={"API_KEY": "bd57efec9a21480a98b8fe1b6229ff43ec6b4628"},
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

            yield item

        if response.json()["per_page"] * response.meta["page"] < response.json()["total"]:
            yield self.make_request(response.meta["page"] + 1)
