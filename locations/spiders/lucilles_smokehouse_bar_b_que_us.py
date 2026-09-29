import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class LucillesSmokehouseBarBQueUSSpider(Spider):
    name = "lucilles_smokehouse_bar_b_que_us"
    item_attributes = {"brand": "Lucille's Smokehouse BBQ", "brand_wikidata": "Q17019306"}
    start_urls = ["https://lucillesbbq.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@data-location-id and contains(@class, "znt-grid-cell")]'):
            address = location.xpath('./div[contains(@class, "znt-text")]/text()').getall()
            locality = re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5})", address[1])

            item = Feature(
                ref=location.attrib["data-location-id"],
                branch=location.xpath("normalize-space(./h3)").get().replace("Montebelo", "Montebello"),
                street_address=address[0],
                city=locality.group(1),
                state=locality.group(2),
                postcode=locality.group(3),
                country="US",
                phone=address[2],
                website=response.url,
            )

            hours = OpeningHours()
            for hours_text in location.xpath(".//ul/li/text()").getall():
                hours.add_ranges_from_string(hours_text)
            item["opening_hours"] = hours

            item["extras"]["website:menu"] = response.urljoin("/menu")
            if order_url := location.css('a[href^="https://lucillesbbq.olo.com/menu/"]::attr(href)').get():
                item["extras"]["website:orders"] = order_url

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "barbecue"
            yield item
