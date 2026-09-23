from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BbTheatresUSSpider(Spider):
    name = "bb_theatres_us"
    item_attributes = {"name": "B&B Theatres", "brand": "B&B Theatres", "brand_wikidata": "Q4833576"}
    allowed_domains = ["www.bbtheatres.com"]
    start_urls = ["https://www.bbtheatres.com/page-data/our-theatres/page-data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The theatre directory itself is rendered client-side by a Gatsby
        # static query. Its result is cached at a build-hash-named URL that
        # only changes when the site's GraphQL queries change, and that
        # hash is discoverable from this stable page-data.json.
        for query_hash in response.json()["staticQueryHashes"]:
            yield Request(f"https://www.bbtheatres.com/page-data/sq/d/{query_hash}.json", callback=self.parse_theatres)

    def parse_theatres(self, response: Response) -> Any:
        theatres = response.json().get("data", {}).get("allTheater", {}).get("nodes")
        if not theatres:
            return  # this static query result is unrelated to the theatre directory

        for theatre in theatres:
            info = theatre.get("practicalInfo")
            if not info or info.get("closed"):
                continue

            location = info["location"]
            coordinates = info.get("coordinates") or {}

            item = Feature()
            item["ref"] = theatre["id"]
            item["branch"] = theatre["name"]
            item["website"] = f"https://www.bbtheatres.com{theatre['path']}"
            item["street_address"] = location.get("address")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zip")
            item["country"] = theatre.get("country", {}).get("iso31661A2")
            item["lat"] = coordinates.get("latitude")
            item["lon"] = coordinates.get("longitude")
            item["phone"] = info.get("phone")
            # info["email"] is the same national contact address on every
            # theatre, not a branch-specific one, so it is not included.
            if images := info.get("images"):
                item["image"] = images[0].get("url")
            if screens := theatre.get("screens"):
                item["extras"]["screen"] = str(len(screens))

            apply_category(Categories.CINEMA, item)

            yield item
