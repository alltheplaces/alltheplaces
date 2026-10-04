import chompjs
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class RoccosTacosUSSpider(Spider):
    name = "roccos_tacos_us"
    item_attributes = {"brand": "Rocco's Tacos"}
    start_urls = ["https://www.roccostacos.com/store-locator/"]

    def parse(self, response):
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])
        for location in config["locations"]:
            hours_text = " ".join(Selector(text=location["hours"]).xpath("//text()").getall())
            if "coming soon" in hours_text.lower():
                continue
            item = Feature(
                ref=location["slug"],
                branch=location["name"],
                street_address=location["street"],
                city=location["city"],
                state=location["state"],
                postcode=location["postal_code"],
                country="US",
                lat=location["lat"],
                lon=location["lng"],
                phone=location["phone_number"],
                website=response.urljoin(location["url"]),
            )
            # Structured hours disagree with the displayed schedule for Orlando.
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text.replace("|", " "))
            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "mexican"
            yield item
