from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ArbysUSSpider(Spider):
    name = "arbys_us"
    item_attributes = {"brand": "Arby's", "brand_wikidata": "Q630866"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://api.arbys.com/arb/web-exp-api/v1/location?latitude=0&longitude=0&radius=500000&limit=100&page={}".format(
                page
            )
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            if location["contactDetails"]["address"]["countryCode"] == "KR":
                continue  # ArbysCASpider
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["displayName"]
            item["street_address"] = merge_address_lines(
                [
                    location["contactDetails"]["address"]["line1"],
                    location["contactDetails"]["address"]["line2"],
                    location["contactDetails"]["address"]["line3"],
                ]
            )
            item["postcode"] = location["contactDetails"]["address"]["postalCode"]
            item["state"] = location["contactDetails"]["address"]["stateProvinceCode"]
            item["country"] = location["contactDetails"]["address"]["countryCode"]
            item["city"] = location["contactDetails"]["address"]["city"]
            item["phone"] = location["contactDetails"]["phone"]
            item["website"] = "https://www.arbys.com/locations/{}/".format(location["url"])
            item["lat"] = location["details"]["latitude"]
            item["lon"] = location["details"]["longitude"]

            yield item

        metadata = response.json()["metadata"]
        if metadata["isLastPage"] is False:
            yield self.make_request(metadata["pageNumber"] + 1)
