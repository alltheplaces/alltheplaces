import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class CrackerBarrelSpider(SitemapSpider):
    name = "crackerbarrel"
    item_attributes = {"brand": "Cracker Barrel", "brand_wikidata": "Q4492609"}
    allowed_domains = ["crackerbarrel.com"]
    sitemap_urls = ["https://www.crackerbarrel.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/crackerbarrel\.com\/Locations\/States\/(\w{2})\/([-\w]+)\/(\d+)$",
            "parse_store",
        )
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace(
                "https://crackerbarrel.com/sitecore/shell/crackerbarrel/brandsite/home/",
                "https://www.crackerbarrel.com/",
            )
            yield entry

    def parse_store(self, response):
        ldjson = response.xpath('//script[@type="application/json"]/text()').get()
        data = json.loads(ldjson)["sitecore"]["route"]["fields"]

        hours = OpeningHours()
        for day in DAYS:
            start_time = data[f"{day}_Open"]["value"]
            end_time = data[f"{day}_Close"]["value"]
            hours.add_range(day[:2], start_time, end_time, "%H:%M %p")

        properties = {
            "ref": data["Store Number"]["value"],
            "lat": data["Latitude"]["value"],
            "lon": data["Longitude"]["value"],
            "website": response.url,
            "name": data["Alternate Name"]["value"],
            "street_address": data["Address 1"]["value"],
            "city": data["City"]["value"],
            "state": data["State"]["value"],
            "postcode": data["Zip"]["value"],
            "country": data["Country"]["value"],
            "phone": data["Phone"]["value"],
            "opening_hours": hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
