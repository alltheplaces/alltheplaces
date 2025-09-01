from typing import Iterable

from scrapy.http import FormRequest
from scrapy.spiders import Request

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class FullersGBSpider(JSONBlobSpider):
    name = "fullers_gb"
    item_attributes = {
        "brand": "Fuller's",
        "brand_wikidata": "Q5253950",
    }

    custom_settings = {
        "COOKIES_ENABLED": True,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    locations_key = ["items"]
    requires_proxy = True


    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url="https://www.fullers.co.uk/api/main/pubs/feed",
            formdata={
                "pageNumber": str(page),
                "latitude": "0",
                "longitude": "0",
                "categories": [],
                "area": "D61B5F3C29994C99A3C93FA4144315A9",
            },
            method="POST",
            headers={
                "Host": "www.fullers.co.uk",
                "Accept": "application/json",
            },
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature["pubId"]
