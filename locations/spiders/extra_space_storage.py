import json
import re

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class ExtraSpaceStorageSpider(SitemapSpider):
    name = "extra_space_storage"
    item_attributes = {"brand": "Extra Space Storage", "brand_wikidata": "Q5422162"}
    allowed_domains = ["www.extraspace.com"]

    # Seems to be sufficient to allow the site to include correct ldjson
    custom_settings = {"DOWNLOAD_DELAY": 1.6}

    sitemap_urls = ["https://www.extraspace.com/facility-sitemap.xml"]
    sitemap_rules = [(r"/facilities/", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            # Sitemap contains subpages but not the main location
            entry["loc"] = re.sub("/id/.*", "/", entry["loc"])
            yield entry

    def parse(self, response):
        try:
            data = self.get_json_data(response)
        except TypeError:
            yield get_retry_request(response.request, spider=self, reason="missing ldjson")
            return

        data_address = data["address"]
        data_geo = data["geo"]

        opening_hours = OpeningHours()
        for row in data["openingHours"]:
            day, interval = row.split(" ", 1)
            open_time, close_time = interval.split("-", 1)
            opening_hours.add_range(day, open_time, close_time)

        properties = {
            "ref": response.url.split("/")[-2],
            "name": data["name"],
            "street_address": data_address["streetAddress"],
            "city": data_address["addressLocality"],
            "state": data_address["addressRegion"],
            "postcode": data_address["postalCode"],
            "lon": float(data_geo["longitude"]),
            "lat": float(data_geo["latitude"]),
            "phone": data["telephone"],
            "website": data["url"],
            "opening_hours": opening_hours.as_opening_hours(),
        }

        yield Feature(**properties)

    def get_json_data(self, response):
        # Note: Page omits the good ldjson when given a browser user-agent
        # But also sporadically for no reason
        ldjson = response.xpath('//script[@id="JsonLdSelfStorageScript"]/text()')
        data = json.loads(ldjson.get())
        assert data["@type"] == "SelfStorage"
        return data
