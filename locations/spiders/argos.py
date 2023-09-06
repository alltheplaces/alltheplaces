import json
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class ArgosSpider(SitemapSpider):
    name = "argos"
    item_attributes = {"brand": "Argos", "brand_wikidata": "Q4789707"}
    allowed_domains = ["www.argos.co.uk"]
    download_delay = 0.5
    sitemap_urls = ["https://www.argos.co.uk/stores_sitemap.xml"]
    sitemap_rules = [(r"https://www.argos.co.uk/stores/([\d]+)-([\w-]+)", "parse")]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse(self, response):
        data = re.findall(r"window.INITIAL_STATE =[^<]+", response.text)
        json_data = json.loads(data[0].replace("window.INITIAL_STATE =", ""))
        properties = {
            "street_address": json_data["store"]["store"]["address"],
            "phone": json_data["store"]["store"]["tel"],
            "city": json_data["store"]["store"]["town"],
            "name": json_data["store"]["store"]["name"],
            "postcode": json_data["store"]["store"]["postcode"],
            "ref": json_data["store"]["store"]["id"],
            "website": response.url,
            "lat": float(json_data["store"]["store"]["lat"]),
            "lon": float(json_data["store"]["store"]["lng"]),
            "extras": {
                "store_type": json_data["store"]["store"]["type"],
            },
        }

        oh = OpeningHours()
        for item in json_data["store"]["store"]["storeTimes"]:
            open_time, close_time = item["time"].split(" - ")
            if open_time and not open_time.isspace() and close_time and not close_time.isspace():
                oh.add_range(item["date"][:2], open_time, close_time)

        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
