import json
import re
from urllib.parse import urljoin

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class GreyhoundSpider(SitemapSpider):
    name = "greyhound"
    item_attributes = {"brand": "Greyhound", "brand_wikidata": "Q755309"}
    allowed_domains = ["greyhound.com"]
    sitemap_urls = ["https://www.greyhound.com/robots.txt"]
    sitemap_rules = [
        # City page, may contain multiple stations
        # e.g. https://www.greyhound.com/bus/new-york-ny
        (r"^https://www\.greyhound\.com/bus/[-\w]+$", "parse")
        # No need to download station page. City page has all needed info
        # e.g. https://www.greyhound.com/bus/new-york-ny/new-york-city-chinatown-bowery-canal-st
    ]

    def parse(self, response):
        # The richest data is JSON in an inline script call to handleStopsLocation()
        for script in response.css("script"):
            script = script.get()
            # Extract first function argument
            m = re.search(r"handleStopsLocation\((.*\]),.*?\);\n", script)
            if m:
                stations = m.group(1)
                break

        if not stations:
            # Page probably says "This destination is currently unavailable."
            return
        stations = json.loads(stations)

        for station in stations:
            item = Feature()
            item["lat"] = station["Lat"]
            item["lon"] = station["Lon"]
            item["ref"] = station["Key"]
            item["branch"] = station["Name"]
            item["street_address"] = station["Address"]
            item["city"], item["state"] = station["AddressCity"].split(", ")
            item["postcode"] = station["Zip"]
            # Phone number is brand-wide
            # item["phone"] = station["Phone"]
            item["website"] = urljoin(response.url, station["PagePath"])

            apply_category(Categories.BUS_STATION, item)
            yield item
