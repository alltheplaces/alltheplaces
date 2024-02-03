import re

import scrapy

from locations.items import Feature


class MontessoriSchoolSpider(scrapy.Spider):
    name = "montessori_school"
    item_attributes = {"brand": "Montessori School", "extras": {"amenity": "school"}}
    allowed_domains = ["www.montessori.com"]
    start_urls = ("https://www.montessori.com/montessori-schools/find-a-school/",)

    def parse(self, response):
        for state_path in response.xpath('//map[@id="USMap"]/area/@href'):
            yield scrapy.Request(
                response.urljoin(state_path.extract()),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for school_elem in response.xpath('//div[@class="locationCard"]'):
            addr_elem = school_elem.xpath('.//a[@class="addrLink addrLinkToMap"]/span[@class="addr"]')
            city_state_str = addr_elem.xpath('.//span[@class="cityState"]/text()').extract_first()
            (city, state, postcode) = re.search(r"^(.*), ([A-Z]{2}) (\d{5})$", city_state_str).groups()

            properties = {
                "ref": school_elem.xpath("@data-school-id")[0].extract(),
                "name": school_elem.xpath('.//a[@class="schoolNameLink"]/text()').extract_first(),
                "street_address": addr_elem.xpath('.//span[@class="street"]/text()').extract_first().strip(),
                "city": city,
                "state": state,
                "postcode": postcode,
                "lon": float(addr_elem.xpath(".//@data-longitude").extract_first()),
                "lat": float(addr_elem.xpath(".//@data-latitude").extract_first()),
            }

            yield Feature(**properties)
