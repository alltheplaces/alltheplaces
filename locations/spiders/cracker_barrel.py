import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class CrackerBarrelSpider(SitemapSpider):
    name = "cracker_barrel"
    item_attributes = {"brand": "Cracker Barrel", "brand_wikidata": "Q4492609"}
    allowed_domains = ["crackerbarrel.com"]
    sitemap_urls = ["https://www.crackerbarrel.com/sitemap.xml"]
    sitemap_rules = [(r"\/Locations\/States\/(\w{2})\/([-\w]+)\/(\d+)$", "parse_store")]
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("https://crackerbarrel.com/", "https://www.crackerbarrel.com/")
            yield entry

    def parse_store(self, response):
        ldjson = response.xpath('//script[@type="application/json"]/text()').get()
        data = json.loads(ldjson)["sitecore"]["route"]["fields"]

        hours = OpeningHours()
        for day in DAYS_FULL:
            start_time = data[f"{day}_Open"]["value"]
            end_time = data[f"{day}_Close"]["value"]
            hours.add_range(day[:2], start_time, end_time, "%I:%M %p")

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
        apply_category(Categories.RESTAURANT, properties)
        apply_category({"cuisine": "american"}, properties)
        yield Feature(**properties)
