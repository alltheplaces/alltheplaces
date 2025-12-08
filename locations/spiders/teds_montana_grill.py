import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TedsMontanaGrillSpider(scrapy.Spider):
    name = "teds_montana_grill"
    allowed_domains = ["www.tedsmontanagrill.com"]
    item_attributes = {"brand": "Ted's Montana Grill", "brand_wikidata": "Q16953170"}
    start_urls = ("https://www.tedsmontanagrill.com/locations.html",)

    def parse(self, response):
        location_selectors = response.xpath('.//div[@class="location-list-item"]')
        for location_selector in location_selectors[:]:
            if location_selector.xpath(".//h3/text()").extract_first():
                state = location_selector.xpath(".//h3/text()").extract_first()
            yield from self.parse_location(location_selector, state)

    def parse_location(self, location, state):
        ref = location.xpath(".//a/@href").extract_first()
        city = location.xpath(".//h5/text()").extract_first()
        phone = location.xpath(".//p")[-1].xpath(".//span/a/@href").extract_first().replace("tel:", "")
        address = location.xpath(".//p")[-1].xpath("text()").extract()
        street_address = clean_address([line.strip() for line in address[:-1]])
        postcode = address[-1].strip()
        addr_full = f"{street_address}, {postcode}"
        properties = {
            "ref": ref,
            "state": state,
            "city": city,
            "phone": phone,
            "street_address": street_address,
            "postcode": postcode,
            "addr_full": addr_full,
        }
        yield Feature(**properties)
