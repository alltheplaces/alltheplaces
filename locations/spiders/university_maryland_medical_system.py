import json
import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class UniversityMarylandMedicalSystemSpider(SitemapSpider):
    name = "university_maryland_medical_system"
    item_attributes = {"brand": "University of Maryland Medical System"}
    sitemap_urls = ["https://www.umms.org/sitemap.ashx"]
    sitemap_rules = [(r"/[^/]+/locations/[^/]+$", "parse_location")]

    def parse_location(self, response):
        data = json.loads(response.xpath('//div[contains(@class, "locations")]/@data-map-json').get())
        addr_last_line = data["items"][0]["address2"]
        city, state, zipcode = re.search(
            r"^(.*),\s+([a-z]{2}|Maryland)\s+([0-9]+)\s*$", addr_last_line, re.IGNORECASE
        ).groups()

        ref = "_".join(re.search(r".+/(.+)/.+/(.+)", response.url).groups())

        properties = {
            "name": data["items"][0]["title"],
            "ref": ref,
            "addr_full": data["items"][0]["address1"],
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": data["items"][0]["phone"],
            "website": response.url,
            "lat": float(data["items"][0]["coordinates"][0]["lat"]),
            "lon": float(data["items"][0]["coordinates"][0]["lng"]),
        }
        yield Feature(**properties)
