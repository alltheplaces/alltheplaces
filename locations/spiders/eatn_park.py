import json
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature

HOURS_RE = re.compile(r"(?P<day>\w+) (?P<open_time>\S+) - (?P<close_time>\S+)")


class EatnParkSpider(SitemapSpider):
    name = "eatn_park"
    item_attributes = {"brand": "Eat'n Park", "brand_wikidata": "Q5331211"}
    sitemap_urls = ["https://locations.eatnpark.com/robots.txt"]
    sitemap_rules = [(r"/restaurants-", "parse")]

    def parse(self, response):
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()')
        [data] = json.loads(ldjson.get())

        opening_hours = OpeningHours()
        for m in HOURS_RE.finditer(data["openingHours"]):
            g = m.groupdict()
            opening_hours.add_range(g["day"], g["open_time"], g["close_time"])

        properties = {
            "ref": re.search(r"-(\d+)\.html", response.url).group(1),
            "website": response.url,
            "name": response.css("span.location-name::text").get(),
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "opening_hours": opening_hours.as_opening_hours(),
            "phone": data["address"]["telephone"],
        }
        yield Feature(**properties)
