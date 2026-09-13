import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# The source data usually gives state abbreviations (e.g. "VIC") but at
# least one store uses the full name instead, so normalise it.
STATES = {
    "new south wales": "NSW",
    "victoria": "VIC",
    "queensland": "QLD",
    "western australia": "WA",
    "south australia": "SA",
    "tasmania": "TAS",
    "australian capital territory": "ACT",
    "northern territory": "NT",
}


class GhandaAUSpider(Spider):
    name = "ghanda_au"
    item_attributes = {"brand": "Ghanda", "brand_wikidata": "Q105960946"}
    allowed_domains = ["ghanda.com"]
    start_urls = ["https://ghanda.com/store-finder"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.find_json_file)

    def find_json_file(self, response: Response) -> Any:
        build_id = (
            response.xpath('//script[contains(@src, "/_buildManifest.js")]/@src')
            .get()
            .replace("/_next/static/", "")
            .replace("/_buildManifest.js", "")
        )
        yield JsonRequest(f"https://ghanda.com/_next/data/{build_id}/en-US/store-finder.json")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["pageProps"]["pageData"]:
            data = location["data"]

            item = Feature()
            item["ref"] = location["uid"]
            item["website"] = "https://ghanda.com/stores/" + location["uid"]

            if name := data.get("name"):
                item["name"] = name[0]["text"].title()

            item["street_address"] = ", ".join(
                filter(None, (line.strip() for line in data.get("street_address", "").split("\n")))
            )
            item["city"] = data.get("suburb")
            item["postcode"] = data.get("postcode")
            if state := data.get("state"):
                item["state"] = STATES.get(state.lower(), state)
            item["country"] = "AU"
            item["phone"] = data.get("phone")

            if geo := data.get("geolocation"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")

            item["opening_hours"] = OpeningHours()
            for rule in data.get("hours", []):
                text = rule.get("text", "").strip()
                if m := re.match(
                    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2}:\d{2})\s*([ap]m)\s*-\s*(\d{1,2}:\d{2})\s*([ap]m)$",
                    text,
                    re.IGNORECASE,
                ):
                    day, open_time, open_ampm, close_time, close_ampm = m.groups()
                    item["opening_hours"].add_range(
                        day,
                        f"{open_time}{open_ampm}",
                        f"{close_time}{close_ampm}",
                        time_format="%I:%M%p",
                    )

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
