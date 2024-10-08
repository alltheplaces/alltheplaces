import re

from scrapy import Spider
from scrapy.selector import Selector

from locations.items import Feature

matcher = re.compile(
    r"position: \{lat: ([0-9.-]+),\s*"
    r"lng: ([0-9.-]+)\},\s*"
    r"map: bbdMap,\s*"
    r"icon: image,\s*"
    r"title: '([^']+) Black Bear Diner'\s*"
    r"\}\);\s*"
    r"google\.maps\.event\.addListener\(marker, 'click', function \(\)\{\s*"
    r"var contentString = '([^']+)';\s*"
    r"contentString \+= '([^']+)';",
    flags=re.S,
)


class BlackBearDinerUSSpider(Spider):
    name = "black_bear_diner_us"
    item_attributes = {"brand": "Black Bear Diner", "brand_wikidata": "Q4920343"}
    start_urls = ["https://blackbeardiner.com/locations/"]

    def parse(self, response):
        for match in matcher.findall(response.text):
            address = [line.removeprefix("\\") for line in Selector(text=match[3]).xpath("//address/text()").getall()]
            city, state = address[1].split(", ")
            link = Selector(text=match[4]).xpath("//@href").get()
            yield Feature(
                lat=match[0],
                lon=match[1],
                branch=match[2],
                street_address=address[0],
                city=city,
                state=state,
                postcode=address[2],
                phone=address[3],
                website=link,
                ref=link,
            )
