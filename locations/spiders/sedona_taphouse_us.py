import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SedonaTaphouseUSSpider(Spider):
    name = "sedona_taphouse_us"
    item_attributes = {"brand": "Sedona Taphouse"}
    allowed_domains = ["djbhospitality.com"]
    start_urls = ["https://djbhospitality.com/locations/"]

    def parse(self, response: Response) -> Iterable[Request]:
        websites = {}
        for url in response.xpath('//a[contains(@href, "sedonataphouse.com/locations/")]/@href').getall():
            url = url.replace("http://", "https://")
            ref = url.rstrip("/").rsplit("/", 1)[-1]
            websites[ref] = url

        yield Request(
            "https://djbhospitality.com/wp-json/wpgmza/v1/markers",
            callback=self.parse_markers,
            cb_kwargs={"websites": websites},
        )

    def parse_markers(self, response: Response, websites: dict[str, str]) -> Iterable[Feature]:
        markers = {}
        for marker in response.json():
            if marker.get("map_id") != "2" or "Sedona Taphouse" not in marker.get("title", ""):
                continue

            branch = marker["title"].split(" - Sedona Taphouse", 1)[0]
            location = branch if re.search(r", [A-Z]{2}$", branch) else marker.get("description", "")
            match = re.search(r"^(.*), ([A-Z]{2})$", location)
            if not match:
                continue

            city, state = match.groups()
            city = city.split("-", 1)[0]
            link = marker.get("link", "")
            if match := re.search(r"/locations/([^/]+)", link):
                ref = match.group(1)
            else:
                ref = re.sub(r"[^a-z0-9]+", "-", location.lower()).strip("-")
            if ref not in websites:
                continue

            marker["branch"] = branch
            marker["city"] = city
            marker["state"] = state
            markers[ref] = marker

        for ref, marker in markers.items():
            address = marker.get("address", "").replace("\u200b", "").strip()
            postcode = re.search(r"\b\d{5}(?:-\d{4})?\b(?=(?:,? USA)?$)", address)
            item = Feature(
                ref=ref,
                branch=marker["branch"],
                addr_full=address,
                city=marker["city"],
                state=marker["state"],
                postcode=postcode.group() if postcode else None,
                country="US",
                lat=marker["lat"],
                lon=marker["lng"],
                website=websites[ref],
            )
            apply_category(Categories.RESTAURANT, item)
            yield item
