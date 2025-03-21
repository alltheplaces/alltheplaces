from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class MitsubishiPLSpider(Spider):
    name = "mitsubishi_pl"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi.pl/dealerzy"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Fetch cookie
        user_session = ""
        for cookie in response.headers.getlist("Set-Cookie"):
            if b"user_session" in cookie:
                user_session = cookie.split(b"=")[1].split(b";")[0].decode("utf-8")
                break

        token = response.xpath('//meta[@name="csrf-token"]/@content').get()

        yield FormRequest(
            url="https://www.mitsubishi.pl/api/modules/dealers/markers/pl",
            headers={"x-csrf-token": token},
            cookies={"user_session": user_session},
            formdata={"filters[region]": "", "filters[query]": ""},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location["street"] = location.pop("address_street", "")
            item = DictParser.parse(location)
            item["lat"] = location.get("marker_lat")
            item["lon"] = location.get("marker_lng")
            item["housenumber"] = location.get("address_number")
            item["postcode"] = location.get("address_postal")
            item["phone"] = location.get("address_phone") or location.get("service_phone")
            yield item
