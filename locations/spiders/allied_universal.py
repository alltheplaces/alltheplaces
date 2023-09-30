import scrapy

from locations.items import Feature


class AlliedUniversalSpider(scrapy.Spider):
    name = "allied_universal"
    allowed_domains = ["www.aus.com"]
    item_attributes = {"brand": "Allied Universal", "brand_wikidata": "Q4732537"}
    start_urls = ("https://www.aus.com/offices",)

    def parse(self, response):
        location_selectors = response.xpath('.//div[@class="Addr"]')
        for location_selector in location_selectors[:]:
            yield from self.parse_location(location_selector)

    def parse_location(self, location):
        ref = location.xpath('.//div[@class="Address-1"]/text()').extract_first().strip()
        street_address = (
            location.xpath('.//div[@class="Address-1"]/text()').extract_first().strip()
            + ", "
            + location.xpath('.//div[@class="Address-2"]/text()').extract_first().strip()
        )
        postcode = location.xpath('.//span[@class="Zip"]/text()').extract_first().strip()
        city = location.xpath('.//span[@class="City"]/text()').extract_first().strip()
        state = location.xpath('.//span[@class="State"]/text()').extract_first().strip()
        country = location.xpath('.//div[@class="Country"]/text()').extract_first().strip()
        if not country and state != "PR":
            country = "US"
        elif not country and state == "PR":
            country = "PR"
            state = None
        elif country == "U.S. Virgin Islands":
            country = "VI"
            state = None
        elif country == "United Kingdom":
            state = None
        elif country == "Australia" and state == "New Zealand":
            country = "NZ"
            state = None
        phone = location.xpath('.//div[@class="PhoneNum"]/text()').extract_first().replace(".", "-").strip()
        website = location.xpath(".//a/@href").extract_first()
        if website:
            if website[0] == "/":
                website = "https://www.aus.com" + website
        properties = {
            "ref": ref,
            "street_address": street_address,
            "postcode": postcode,
            "city": city,
            "state": state,
            "country": country,
            "phone": phone,
            "website": website,
        }
        yield Feature(**properties)
