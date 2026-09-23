import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ShaverShopSpider(JSONBlobSpider):
    name = "shaver_shop"
    item_attributes = {"brand": "Shaver Shop", "brand_wikidata": "Q119443589"}
    start_urls = [
        "https://www.shavershop.com.au/on/demandware.store/Sites-Shaver_Shop_au-Site/en_AU/Stores-GetAllStores?countryCode=AU",
        "https://www.shavershop.co.nz/on/demandware.store/Sites-Shaver_Shop_nz-Site/en_NZ/Stores-GetAllStores?countryCode=NZ",
    ]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "shavershop.co.nz" in response.url:
            item["website"] = (
                "https://www.shavershop.co.nz/stores/"
                + feature["stateCode"]
                + "/"
                + feature["city"]
                + "/"
                + feature["id"]
            ).replace(" ", "%20")
            item.pop("state")
        else:
            item["website"] = "https://www.shavershop.com.au/stores/" + feature["stateCode"] + "/" + feature["id"]
        hours_string = re.sub(r"\s+", " ", feature["storeHours"].replace("<br />", "").replace("<p>", "")).strip()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
