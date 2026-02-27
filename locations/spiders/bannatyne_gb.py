import json

import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media


class BannatyneGBSpider(scrapy.Spider):
    name = "bannatyne_gb"
    item_attributes = {
        "brand": "Bannatyne Health Club",
        "brand_wikidata": "Q24993691",
    }
    start_urls = ["https://www.bannatyne.co.uk/health-club/all-locations"]

    def parse(self, response):
        for club in response.xpath("//*[@data-attributes]"):
            data = json.loads(club.attrib["data-attributes"])
            item = Feature()
            item["ref"] = data["id"]
            item["branch"] = data.get("name")
            item["lat"] = data.get("latitude")
            item["lon"] = data.get("longitude")
            item["phone"] = data.get("telephone")
            item["email"] = data.get("email")
            item["website"] = f"https://www.bannatyne.co.uk/health-club/{data['slug']}"

            item["addr_full"] = (
                data.get("address", "")
                .removeprefix("Bannatyne Health Club & Spa, ")
                .removeprefix("Bannatyne Health Club and Spa, ")
                .removeprefix("Bannatyne Health Club, ")
            )

            set_social_media(item, SocialMedia.FACEBOOK, data.get("facebook"))
            set_social_media(item, SocialMedia.INSTAGRAM, data.get("instagram"))

            if open_times := data.get("open_times"):
                oh = OpeningHours()
                oh.add_ranges_from_string(" ".join(Selector(text=open_times).xpath("//text()").getall()))
                item["opening_hours"] = oh

            apply_category(Categories.GYM, item)
            yield item
