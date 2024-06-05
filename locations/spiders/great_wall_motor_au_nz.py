import csv

from scrapy import Request, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class GreatWallMotorAUNZSpider(Spider):
    name = "great_wall_motor_au_nz"
    item_attributes = {"brand": "Great Wall Motor", "brand_wikidata": "Q1117001", "extras": Categories.SHOP_CAR.value}
    allowed_domains = ["api.storyblok.com", "a.storyblok.com"]
    start_urls = [
        "https://api.storyblok.com/v2/cdn/stories/dealer-locator?cv=1715928712&language=au&resolve_relations=SelectModelLine.options%2CSelectEnquiryType.options&token=grBrbRuRX6NJLbQcyDGpcgtt&version=published"
    ]

    def parse(self, response):
        locations_csv_url = response.json()["story"]["content"]["body"][0]["stores"]["filename"]
        yield Request(url=locations_csv_url, callback=self.parse_locations)

    def parse_locations(self, response):
        reader = csv.DictReader(response.text.splitlines())
        for location in reader:
            item = DictParser.parse(location)
            item["ref"] = location["Dealer code"]
            item["name"] = location["Dealer Name"]
            item["street_address"] = item.pop("addr_full", None)
            if location["Country"] != "NZ":
                item["state"] = location["State/Region"]
            item["postcode"] = location["Post Code"]
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if day_hours := location.get(day_name):
                    if day_hours == "Closed":
                        continue
                    item["opening_hours"].add_range(day_name, *day_hours.split(" - ", 1), "%I:%M %p")
            yield item
