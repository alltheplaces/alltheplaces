import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class CarrefourBESpider(scrapy.Spider):
    name = "carrefour_be"
    start_urls = ["https://winkels.carrefour.be/api/v3/locations"]
    brands = {
        "express": ("Carrefour Express", "Q2940190", Categories.SHOP_CONVENIENCE),
        "orange": ("Carrefour Express", "Q2940190", Categories.SHOP_CONVENIENCE),
        "market": ("Carrefour Market", "Q2689639", Categories.SHOP_SUPERMARKET),
        "hyper": ("Carrefour", "Q217599", Categories.SHOP_SUPERMARKET),
        "drive-2": ("Carrefour", "Q217599", {**Categories.SHOP_SUPERMARKET.value, "drive_through": "yes"}),
    }

    def parse(self, response):
        for data in response.json():
            data["latitude"] = data.get("address").get("latitude")
            data["longitude"] = data.get("address").get("longitude")
            data["id"] = data.get("externalId")

            item = DictParser.parse(data)

            brand_slug = data.get("brandSlug")
            brand, brand_wikidata, category = self.brands[brand_slug]
            item["brand"] = brand
            item["brand_wikidata"] = brand_wikidata
            if category is not None:
                apply_category(category, item)

            oh = OpeningHours()
            for index, bH in enumerate(data.get("businessHours")):
                oh.add_range(DAYS_FULL[index - 1], bH.get("openTimeFormat"), bH.get("closeTimeFormat"))

            item["opening_hours"] = oh.as_opening_hours()
            item["website"] = "https://winkels.carrefour.be/nl/s/carrefour/{slug}/{id}".format(
                slug=data.get("slug"), id=data.get("externalId")
            )

            yield item
