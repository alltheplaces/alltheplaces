import re
import json

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class ArgosSpider(SitemapSpider):
    name = "argos"
    item_attributes = {"brand": "Argos"}
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
            "addr_full": json_data["store"]["store"]["address"],
            "phone": json_data["store"]["store"]["tel"],
            "city": json_data["store"]["store"]["town"],
            "state": "",
            "postcode": json_data["store"]["store"]["postcode"],
            "ref": json_data["store"]["store"]["id"],
            "website": response.url,
            "lat": float(json_data["store"]["store"]["lat"]),
            "lon": float(json_data["store"]["store"]["lng"]),
        }

        open_hours = ""
        for item in json_data["store"]["store"]["storeTimes"]:
            open_hours = open_hours + item["date"][:2] + " " + item["time"] + " ;"
        if open_hours:
            properties["opening_hours"] = open_hours

        yield GeojsonPointItem(**properties)
