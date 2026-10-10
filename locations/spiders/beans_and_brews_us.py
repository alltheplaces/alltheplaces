import base64
import json
import re

from scrapy import Request, Spider
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BeansAndBrewsUSSpider(Spider):
    name = "beans_and_brews_us"
    item_attributes = {"brand": "Beans & Brews Coffeehouse", "name": "Beans & Brews Coffeehouse"}
    start_urls = ["https://www.beansandbrews.com/near-me/"]

    def parse(self, response):
        script_url = response.xpath('//script[contains(@data-src, "/litespeed/js/")]/@data-src').get()
        yield Request(script_url, callback=self.parse_locations)

    def parse_locations(self, response):
        encoded_data = re.search(r'window\.wpgmp\.mapdata1="([^"]+)"', response.text).group(1)
        data = json.loads(base64.b64decode(encoded_data))

        for location in data["places"]:
            details = location["location"]
            fields = details["extra_fields"]
            item = Feature(
                ref=fields["%bb_store_id%"],
                street_address=location["title"].strip(),
                city=fields["%city%"],
                state=fields["%state%"],
                postcode=fields["%zip%"],
                country="US",
                lat=details["lat"],
                lon=details["lng"],
                phone=fields["%phone_number%"],
                website=details["redirect_permalink"],
            )

            hours = OpeningHours()
            for line in Selector(text=fields["%business_hours%"].replace("<br />", "<br>")).xpath("//text()").getall():
                hours.add_ranges_from_string(line.strip().replace("06:300AM", "06:30AM"))
            item["opening_hours"] = hours

            apply_category(Categories.CAFE, item)
            yield item
