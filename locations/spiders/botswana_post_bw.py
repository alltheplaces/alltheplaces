import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "BotswanaPost", "operator_wikidata": "Q4948874"}


class BotswanaPostBWSpider(Spider):
    name = "botswana_post_bw"
    allowed_domains = ["botswanapost.post"]
    # Drupal geolocation view listing every branch; each branch page adds its type and opening hours.
    start_urls = ["https://botswanapost.post/branch-network"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css("div.geolocation-location[data-lat]"):
            link = location.css(".views-field-title a")
            item = Feature()
            item["lat"], item["lon"] = location.attrib["data-lat"], location.attrib["data-lng"]
            item["ref"] = link.attrib["href"].rstrip("/").rsplit("/", 1)[-1]
            item["branch"] = link.css("::text").get("").strip()
            item["phone"] = location.css(".views-field-field-telephone .field-content::text").get()
            item["website"] = response.urljoin(link.attrib["href"])
            yield response.follow(link.attrib["href"], callback=self.parse_branch, cb_kwargs={"item": item})

    def parse_branch(self, response: Response, item: Feature) -> Any:
        branch_type = response.css(".field--name-field-branch-type a::text").get("").strip()
        item["extras"]["fax"] = response.css(".field--name-field-fax .field__item::text").get()
        hours = response.css(".field--name-field-opening-hours .field__item::text").get("")
        item["opening_hours"] = self.parse_hours(hours)
        if branch_type and branch_type != "Post Office":
            # Other branch types (e.g. agencies) are recorded but treated as post partners.
            item["extras"]["branch_type"] = branch_type
            item["name"] = item.pop("branch")
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = OPERATOR["operator"]
            item["extras"]["post_office:brand:wikidata"] = OPERATOR["operator_wikidata"]
            apply_category(Categories.GENERIC_POI, item)
        else:
            item.update(OPERATOR)
            apply_category(Categories.POST_OFFICE, item)
        yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        # "0815 - 1600"; no days are given, these are the weekday counter hours.
        oh = OpeningHours()
        if m := re.fullmatch(r"\s*(\d{1,2}):?(\d{2})\s*[-–]\s*(\d{1,2}):?(\d{2})\s*", text):
            oh.add_days_range(DAYS_WEEKDAY, f"{m[1].zfill(2)}:{m[2]}", f"{m[3].zfill(2)}:{m[4]}")
        return oh
