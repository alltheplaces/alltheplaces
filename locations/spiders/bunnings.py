import json
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BunningsSpider(SitemapSpider):
    name = "bunnings"
    requires_proxy = True
    allowed_domains = ["bunnings.com.au", "bunnings.co.nz"]
    sitemap_urls = [
        "https://www.bunnings.com.au/stores.xml",
        "https://www.bunnings.co.nz/stores.xml",
    ]
    sitemap_rules = [(r"/stores/.*/.+$", "parse")]
    item_attributes = {"brand": "Bunnings Warehouse", "brand_wikidata": "Q4997829"}

    def parse(self, response: Response) -> Iterable[Feature]:
        location = json.loads(
            response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        )["props"]["pageProps"]["initialState"]["store"]["data"]
        item = DictParser.parse(location)
        item["ref"] = location["name"]
        item.pop("name", None)
        item["branch"] = location["displayName"]
        item["phone"] = location["address"].get("phone")
        item["email"] = location["address"].get("email")
        if item["country"] == "NZ":
            item.pop("state")
            website_prefix = "https://www.bunnings.co.nz/stores/"
        else:
            item["state"] = location["address"]["region"]["isocode"]
            website_prefix = "https://www.bunnings.com.au/stores/"
        if "urlRegion" in location:
            item["website"] = (
                website_prefix + location["urlRegion"] + "/" + location["displayName"].lower().replace(" ", "-")
            )
        item["extras"]["website:map"] = location.get("mapUrl")

        item["opening_hours"] = OpeningHours()
        for day in location["openingHours"]["weekDayOpeningList"]:
            if (
                not day["closed"]
                and day.get("openingTime")
                and day["openingTime"].get("formattedHour")
                and day.get("closingTime")
                and day["closingTime"].get("formattedHour")
            ):
                item["opening_hours"].add_range(
                    day=day["weekDay"],
                    open_time=day["openingTime"]["formattedHour"],
                    close_time=day["closingTime"]["formattedHour"],
                    time_format="%I:%M %p",
                )

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
