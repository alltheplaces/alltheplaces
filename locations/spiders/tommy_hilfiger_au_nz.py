from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TommyHilfigerAUNZSpider(Spider):
    name = "tommy_hilfiger_au_nz"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    allowed_domains = ["au.tommy.com", "nz.tommy.com"]
    start_urls = ["https://au.tommy.com/stores/index/dataAjax/", "https://nz.tommy.com/stores/index/dataAjax/"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if "au.tommy.com" in response.url:
                country = "au"
            elif "nz.tommy.com" in response.url:
                country = "nz"
            properties = {
                "ref": location["i"],
                "name": location["n"],
                "lat": location["l"],
                "lon": location["g"],
                "addr_full": ", ".join(filter(None, location["a"])),
                "postcode": location["seo_postcode"],
                "phone": location.get("p"),
                "website": f"https://{country}.tommy.com" + location["u"],
            }
            if "oh" in location:
                hours_string = (
                    location["oh"]
                    .replace("0|", "Mo: ")
                    .replace("1|", "Tu: ")
                    .replace("2|", "We: ")
                    .replace("3|", "Th: ")
                    .replace("4|", "Fr: ")
                    .replace("5|", "Sa: ")
                    .replace("6|", "Su: ")
                    .replace("  ", " ")
                )
                properties["opening_hours"] = OpeningHours()
                properties["opening_hours"].add_ranges_from_string(hours_string)
            item = Feature(**properties)
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
