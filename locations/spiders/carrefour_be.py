import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)
from locations.user_agents import CHROME_LATEST


class CarrefourBESpider(scrapy.Spider):
    name = "carrefour_be"
    start_urls = ["https://winkels.carrefour.be/api/v3/locations"]
    brands = {
        "express": CARREFOUR_EXPRESS,
        "orange": CARREFOUR_EXPRESS,
        "market": CARREFOUR_MARKET,
        "hyper": CARREFOUR_SUPERMARKET,
        "drive-2": CARREFOUR_SUPERMARKET,
        "Maxi": CARREFOUR_SUPERMARKET,
    }
    user_agent = CHROME_LATEST
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for data in response.json():
            data["latitude"] = data.get("address").get("latitude")
            data["longitude"] = data.get("address").get("longitude")
            data["id"] = data.get("externalId")

            item = DictParser.parse(data)

            brand_slug = data.get("brandSlug")
            if not parse_brand_and_category_from_mapping(item, brand_slug, self.brands):
                self.crawler.stats.inc_value(f"atp/carrefour_be/unknown_brand/{brand_slug}")
                # Default to supermarket if brand match failed
                apply_category(item, Categories.SHOP_SUPERMARKET)

            if brand_slug == "drive-2":
                apply_yes_no(Extras.DRIVE_THROUGH, item, True)

            oh = OpeningHours()
            for index, business_hours in enumerate(data.get("businessHours")):
                oh.add_range(
                    DAYS_FULL[index - 1], business_hours.get("openTimeFormat"), business_hours.get("closeTimeFormat")
                )

            item["opening_hours"] = oh.as_opening_hours()
            item["website"] = "https://winkels.carrefour.be/nl/s/carrefour/{slug}/{id}".format(
                slug=data.get("slug"), id=data.get("externalId")
            )

            yield item
