import re

from scrapy import Spider
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature

matcher = re.compile(
    r"position:\s*\{\s*lat:\s*(-?\d{1,3}\.\d+)\s*,\s*"
    r"lng:\s*(-?\d{1,3}\.\d+)\s*\}\s*,\s*"
    r"map:\s*bbdMap\s*,\s*"
    r"icon:\s*image\s*,\s*"
    r"title:\s*'([^']+)'\s*"
    r"\}\s*\)\s*;\s*"
    r"google\.maps\.event\.addListener\(marker,\s*'click',\s*function\s*\(\)\s*\{\s*"
    r"var contentString\s*=\s*'([^']+)'\s*;\s*"
    r"contentString\s*\+=\s*'([^']+)'\s*;",
    flags=re.S,
)


class BlackBearDinerUSSpider(Spider):
    name = "black_bear_diner_us"
    item_attributes = {"brand": "Black Bear Diner", "brand_wikidata": "Q4920343"}
    allowed_domains = ["blackbeardiner.com"]
    start_urls = ["https://blackbeardiner.com/locations/"]

    def parse(self, response):
        for match in matcher.findall(response.text):
            branch = match[2].removeprefix("Black Bear Diner").strip("- ")
            if not branch:
                branch = None
            address = [line.removeprefix("\\") for line in Selector(text=match[3]).xpath("//address/text()").getall()]
            city, state = address[1].split(", ")
            link = Selector(text=match[4]).xpath("//@href").get()
            properties = {
                "lat": match[0],
                "lon": match[1],
                "branch": branch,
                "street_address": address[0],
                "city": city,
                "state": state,
                "postcode": address[2],
                "phone": address[3],
                "website": link,
                "ref": link,
            }
            apply_category(Categories.RESTAURANT, properties)
            yield Feature(**properties)
