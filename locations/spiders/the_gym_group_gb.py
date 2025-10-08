import re

from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TheGymGroupGBSpider(Spider):
    name = "the_gym_group_gb"
    item_attributes = {
        "brand": "The Gym",
        "brand_wikidata": "Q48815022",
        "country": "GB",
    }
    allowed_domains = ["www.thegymgroup.com"]
    start_urls = ["https://www.thegymgroup.com/find-a-gym/"]

    def parse(self, response):
        locations_js = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        for location in parse_js_object(locations_js)["props"]["pageProps"]["gymMapData"]:
            properties = {
                "ref": location["gym"]["branchId"],
                "name": location["gym"]["gymName"],
                "lat": location["position"]["lat"],
                "lon": location["position"]["lng"],
                "addr_full": re.sub(r"\s+", " ", location["gym"]["gymAddress"]),
                "website": "https://www.thegymgroup.com" + location["gym"]["gymPageURL"],
            }
            yield Request(url=properties["website"], meta={"item": Feature(**properties)}, callback=self.add_hours)

    def add_hours(self, response):
        item = response.meta["item"]
        hours_string = " ".join(
            filter(None, response.xpath('//div[@id="gym_times_location_section"]//p/text()').getall())
        )
        item["opening_hours"] = OpeningHours()
        if "24 hours, 7 days a week" in hours_string.lower():
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        else:
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
