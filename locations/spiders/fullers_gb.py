import re
from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, JsonRequest, Request, Response

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FullersGBSpider(JSONBlobSpider, StructuredDataSpider):
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
    wanted_types = ["restaurant"]
    requires_proxy = True

    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url="https://www.fullers.co.uk/api/main/pubs/feed",
            formdata={
                "pageNumber": str(page),
                "latitude": "0",
                "longitude": "0",
                "categories": [],
                "area": "",
            },
            method="POST",
            headers={
                "Host": "www.fullers.co.uk",
                "Accept": "application/json",
            },
        )

    async def start(self) -> AsyncIterator[FormRequest]:
        yield self.make_request(1)

    def parse(self, response: Response) -> Iterable[Feature]:
        features = self.extract_json(response)
        for feature in features:
            if feature["link"]:
                yield Request(url=feature["link"], meta={"ref": feature["pubId"]}, callback=self.parse_sd)
            else:
                if feature is None:
                    continue
                feature["id"] = feature["pubId"]
                item = DictParser.parse(feature)
                if feature["subTitle"]:
                    item["addr_full"] = feature["subTitle"]
                if feature["link"]:
                    item["website"] = feature["link"]
                yield JsonRequest(
                    url="https://www.fullers.co.uk/api/main/pubs/information?pubId=" + feature["pubId"],
                    cb_kwargs={"item": item},
                    headers={
                        "Host": "www.fullers.co.uk",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
                    },
                    callback=self.post_process_item_json,
                )

        if response.json()["totalPages"] > response.json()["currentPage"]:
            yield self.make_request(int(response.json()["currentPage"]) + 1)

    def post_process_item_json(self, response, item):
        item["lat"] = response.json()["googleMaps"]["coords"]["lat"]
        item["lon"] = response.json()["googleMaps"]["coords"]["lng"]
        item["phone"] = response.json()["socials"]["phoneNumber"]["value"]
        item["email"] = response.json()["socials"]["email"]["value"]
        yield item

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "data-marker-lat" in response.text:
            item["lat"] = re.search(r'data-marker-lat="(-?\d+\.\d+)"', response.text).group(1)
            item["lon"] = re.search(r'data-marker-lng="(-?\d+\.\d+)"', response.text).group(1)
        item["ref"] = response.meta["ref"]
        yield item
