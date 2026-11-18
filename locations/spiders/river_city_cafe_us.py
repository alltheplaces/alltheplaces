from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class RiverCityCafeUSSpider(Spider):
    name = "river_city_cafe_us"
    item_attributes = {"brand": "River City Cafe"}
    start_urls = ["https://rivercitycafe.com/locations/"]

    def parse(self, response):
        for link in response.css('a[href^="tel:"]'):
            address = link.xpath("../preceding-sibling::div[1]").css(".et_pb_blurb_description p")
            lines = [text.strip() for text in address.xpath(".//text()").getall() if text.strip()]
            if not lines:
                continue
            city, region = lines[-1].rsplit(",", 1)
            state, postcode = region.split()
            phone = link.attrib["href"].removeprefix("tel:")
            item = Feature(
                ref=phone,
                addr_full=", ".join(lines),
                city=city,
                state=state,
                postcode=postcode,
                country="US",
                phone=phone,
                website=response.url,
            )
            apply_category(Categories.RESTAURANT, item)
            yield item
