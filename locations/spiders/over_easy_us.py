import html
import json

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class OverEasyUSSpider(Spider):
    name = "over_easy_us"
    item_attributes = {"brand": "Over Easy"}
    start_urls = ["https://eatatovereasy.com/locations/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    postcode_corrections = {150050: "85383"}

    def parse(self, response: Response):
        item_list = next(
            json.loads(script)
            for script in response.css('script[type="application/ld+json"]::text').getall()
            if '"ItemList"' in script
        )
        phones_by_url = {entry["item"]["url"]: entry["item"].get("telephone") for entry in item_list["itemListElement"]}

        script = response.xpath('//script[contains(text(), "const LOCATIONS_CONNECTOR_DATA")]/text()').get()
        locations = chompjs.parse_js_object(script.split("const LOCATIONS_CONNECTOR_DATA =", 1)[1])

        for location in locations:
            item = Feature(
                ref=str(location["id"]),
                branch=html.unescape(location["title"]).strip(),
                street_address=location["address1"].strip(),
                city=location["city"].strip(),
                state=location["state"].strip(),
                postcode=self.postcode_corrections.get(location["id"], location["postal_code"].strip()),
                country="US",
                phone=location["phone"].strip() or phones_by_url.get(location["permalink"]),
                lat=location["latitude"],
                lon=location["longitude"],
                website=location["permalink"],
            )

            hours = OpeningHours()
            hours.add_ranges_from_string(location["hours"])
            item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            yield item
