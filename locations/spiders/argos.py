import re
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.spiders import SitemapSpider


class ArgosSpider(SitemapSpider):
    name = "argos"
    item_attributes = {"brand": "Argos", "brand_wikidata": "Q4789707"}
    allowed_domains = ["www.argos.co.uk"]
    download_delay = 0.5
    sitemap_urls = [
        "https://www.argos.co.uk/stores_sitemap.xml",
    ]
    sitemap_rules = [
        (
            r"https://www.argos.co.uk/stores/([\d]+)-([\w-]+)",
            "parse",
        ),
    ]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

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
            if (
                open_time
                and not open_time.isspace()
                and close_time
                and not close_time.isspace()
            ):
                oh.add_range(item["date"][:2], open_time, close_time)

        properties["opening_hours"] = oh.as_opening_hours()

        yield GeojsonPointItem(**properties)
