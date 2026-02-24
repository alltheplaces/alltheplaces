from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class CisalfaSportITSpider(JSONBlobSpider):
    name = "cisalfa_sport_it"
    item_attributes = {"brand": "Cisalfa Sport", "brand_wikidata": "Q113535511"}
    locations_key = "stores"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.retailtune.com/storelocator/it/?rt_api_key=LgLwP3qejs1nUXFMt4rNSyZO5Iif0pXVw9wUmlcaWRe40uYfXqekTj7SytclsWxuHwBhHiHn7bwxttY9hMdFbv9uNu0jK44bJ1Bs",
            headers={
                "Origin": "https://www.cisalfasport.it",
                "Referer": "https://www.cisalfasport.it/",
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"].startswith("Cisalfa Outlet "):
            item["branch"] = item.pop("name").removeprefix("Cisalfa Outlet ")
            item["name"] = "Cisalfa Outlet"
        else:
            item["branch"] = item.pop("name").removeprefix("Cisalfa Sport ")
        item["state"] = item["state"]["name"]
        yield item
