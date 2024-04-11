import json
import re
from typing import Any
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WaitroseSpider(SitemapSpider):
    name = "waitrose"
    LITTLE_WAITROSE = {"brand": "Little Waitrose", "brand_wikidata": "Q771734"}
    WAITROSE = {"brand": "Waitrose", "brand_wikidata": "Q771734"}
    item_attributes = WAITROSE
    sitemap_urls = ["https://www.waitrose.com/robots.txt"]
    sitemap_follow = ["find-a-store"]
    sitemap_rules = [("/find-a-store/", "parse")]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        props = json.loads(
            unquote(re.search(r"pageProps: JSON\.parse\(decodeURIComponent\(\"(.+)\"\)\),", response.text).group(1))
        )
        if props["document"]["__"]["name"] != "location":
            return  # Directory

        location = props["document"]
        item = DictParser.parse(location)
        item["lat"] = location["yextDisplayCoordinate"]["latitude"]
        item["lon"] = location["yextDisplayCoordinate"]["longitude"]
        item["branch"] = location["geomodifier"]
        item["phone"] = location["mainPhone"]
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            for times in location["hours"].get(day, {}).get("openIntervals", []):
                item["opening_hours"].add_range(day, times["start"], times["end"])

        services = location.get("services", [])
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby Change Facility" in services)
        apply_yes_no(Extras.ATM, item, "Cash Point" in services)
        apply_yes_no(Extras.TOILETS, item, "Customer Toilets" in services)
        apply_yes_no("sells:lottery", item, "Lottery Counter" in services)
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Trolleys Available" in services)

        for ref in location["ref_listings"]:
            if ref["publisher"] == "FACEBOOK":
                item["facebook"] = ref["listingUrl"]
        item["extras"]["ref:google"] = location["googlePlaceId"]

        if item["name"].startswith("Little Waitrose"):
            item.update(self.LITTLE_WAITROSE)
            item["name"] = "Little Waitrose"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item.update(self.WAITROSE)
            item["name"] = "Waitrose"
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
