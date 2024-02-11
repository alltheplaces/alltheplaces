from scrapy import Selector, Spider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class ClarkRubberAUSpider(Spider):
    name = "clark_rubber_au"
    item_attributes = {
        "brand": "Clark Rubber",
        "brand_wikidata": "Q124003720",
        "extras": Categories.SHOP_HOUSEWARE.value,
    }
    allowed_domains = ["www.clarkrubber.com.au"]
    start_urls = ["https://www.clarkrubber.com.au/files/maps/locations.json"]

    def parse(self, response):
        for location in response.json()["features"]:
            properties = {
                "ref": location["properties"].get("siteID"),
                "name": location["properties"].get("name"),
                "geometry": location["geometry"],
                "addr_full": location["properties"].get("address"),
                "phone": location["properties"].get("phone"),
            }
            hours_html = Selector(text=location["properties"].get("hours"))
            hours_text = " ".join(hours_html.xpath("//text()").getall())
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_text)
            yield Feature(**properties)
