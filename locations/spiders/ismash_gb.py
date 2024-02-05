from urllib.parse import urljoin

from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class IsmashGBSpider(Spider):
    name = "ismash_gb"
    item_attributes = {"brand": "iSmash", "brand_wikidata": "Q42306824"}
    start_urls = ["https://api.ismash.com/app/stores"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["isStore"] != 1:
                continue
            item = Feature()
            item["addr_full"] = location["address"]
            item["email"] = location["contact_email"]
            item["phone"] = location["contact_phone"]
            item["extras"]["ref:google"] = location["googleID"]
            item["ref"] = location["id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["extras"]["contact:yelp"] = urljoin("https://www.yelp.co.uk/biz/", location["yelpID"])

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS[:5], *location["mon_fri"].split("-"))

            yield item
