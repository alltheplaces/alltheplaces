import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BackstubeNOSpider(Spider):
    name = "backstube_no"
    item_attributes = {"brand": "Backstube"}
    start_urls = ["https://backstube.no/visit-us"]

    def parse(self, response):
        for location in response.css(".location-row"):
            name = location.css(".location-info strong::text").get()
            if not name:
                continue
            name = name.strip()

            item = Feature()
            item["ref"] = re.sub(r"\W+", "-", name.lower())
            item["name"] = "Backstube"
            item["branch"] = name
            item["website"] = "https://backstube.no/visit-us"
            item["street_address"] = location.css(".location-info::text").get().strip()

            hours = location.css(".location-hour div::text").getall()
            if hours:
                item["opening_hours"] = OpeningHours()
                hours_string = "; ".join([h.strip() for h in hours if h.strip()])
                item["opening_hours"].add_ranges_from_string(hours_string)

            apply_category(Categories.SHOP_BAKERY, item)
            yield item
