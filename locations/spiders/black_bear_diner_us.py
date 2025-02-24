import re

from scrapy import Spider
from scrapy.selector import Selector

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

matcher = re.compile(
    r"position:\s*\{\s*"
    r"lat:\s*(?P<lat>[0-9.-]+),\s*"
    r"lng:\s*(?P<lng>[0-9.-]+)\s*"
    r"\},\s*"
    r"map:\s*bbdMap,\s*"
    r"icon:\s*image,\s*"
    r"title:\s*'Black Bear Diner'\s*"
    r"\}\s*"
    r"\);\s*"
    r"google\.maps\.event\.addListener\("
    r"marker,\s*"
    r"'click',\s*"
    r"function\s*\(\)\s*\{\s*"
    r"var\s*contentString\s*=\s*'(?P<contentString1>[^']+)';\s*"
    r"contentString\s*\+=\s*'(?P<contentString2>[^']+)';",
    flags=re.S,
)


class BlackBearDinerUSSpider(Spider):
    name = "black_bear_diner_us"
    item_attributes = {"brand": "Black Bear Diner", "brand_wikidata": "Q4920343"}
    start_urls = ["https://blackbeardiner.com/locations/"]

    def parse(self, response):
        for match in matcher.finditer(response.text):
            content = Selector(text=match.group("contentString1") + match.group("contentString2"))
            address = [line.replace("\\", "") for line in content.xpath("//address/text()").getall()]
            city, state = address[1].split(", ")
            link = content.xpath("//a[@class='hours-link']/@href").get()
            yield Feature(
                lat=match.group("lat"),
                lon=match.group("lng"),
                branch=content.xpath("//strong/text()").get().removesuffix(" Black Bear Diner"),
                street_address=address[0],
                city=city,
                state=state,
                addr_full=merge_address_lines(address),
                postcode=address[2],
                phone=content.xpath("//a[starts-with(@href, 'tel')]/text()").get(),
                website=link,
                ref=link,
            )
