from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FirstNationalRealEstateAUSpider(Spider):
    name = "first_national_real_estate_au"
    item_attributes = {"brand": "First National Real Estate", "brand_wikidata": "Q122888198"}
    allowed_domains = ["www.firstnational.com.au"]

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://www.firstnational.com.au/pages/real-estate/offices?widgetKey=200204&context=offices&pattern=offices&pg={}".format(
                page
            )
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["offices"]:
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["office_name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["website"] = response.urljoin(location["office_link"])
            item["phone"] = location["office_phone"]
            item["email"] = location["office_email"]
            item["street_address"] = merge_address_lines(
                [location["office_address_line_1"], location["office_address_line_2"]]
            )
            item["city"] = location["office_suburb"]
            item["postcode"] = location["office_post_code"]
            item["state"] = location["office_state"]

            yield item

        next_page = response.json()["pagination"]["offices"]["next_page"]
        if next_page != 0:
            yield self.make_request(next_page)
