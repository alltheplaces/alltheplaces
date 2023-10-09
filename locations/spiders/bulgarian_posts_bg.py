from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BulgarianPostsBGSpider(Spider):
    name = "bulgarian_posts_bg"
    item_attributes = {"brand": "Bulgarian Posts", "brand_wikidata": "Q2880826"}
    allowed_domains = ["bgpost.bg"]
    start_urls = ["https://bgpost.bg/api/offices?search_by_city_name_or_address="]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json():
            location["street_address"] = location.pop("address", None)
            item = DictParser.parse(location)
            item["name"] = location["office_name"]
            item["city"] = location["city_name"]
            item["state"] = location["district"]
            item["phone"] = location["phone"]
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if location[f"working_hours_{day_name.lower()}"]:
                    item["opening_hours"].add_range(
                        day_name, *location[f"working_hours_{day_name.lower()}"].split("-", 1), "%H:%M"
                    )
            apply_category(Categories.POST_OFFICE, item)
            yield item
