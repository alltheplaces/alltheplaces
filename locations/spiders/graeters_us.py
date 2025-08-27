import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class GraetersUSSpider(SitemapSpider):
    name = "graeters_us"
    item_attributes = {"brand": "Graeter's", "brand_wikidata": "Q5592430"}
    allowed_domains = ["www.graeters.com"]
    sitemap_urls = ["https://www.graeters.com/sitemap.xml"]
    sitemap_rules = [(r"retail-stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//h1[@class="heading h1"]/text()').get().replace("Graeter's ", "")
        item["addr_full"] = response.xpath(
            '//*[@class="store-info__contact-label" and text()="Address"]/following-sibling::span[@class="store-info__contact-value"]/text()'
        ).getall()

        item["phone"] = response.xpath(
            '//*[@class="store-info__contact-label" and text()="Phone"]/following-sibling::span[@class="store-info__contact-value"]/text()'
        ).get()

        item["email"] = response.xpath(
            '//*[@class="store-info__contact-label" and text()="Email"]/following-sibling::span[@class="store-info__contact-value"]/text()'
        ).get()

        item["opening_hours"] = self.parse_hours(
            response.xpath(
                '//*[contains(@class, "store-info__hours-row")]//*[@class="store-info__day"]/text()'
            ).getall(),
            response.xpath(
                '//*[contains(@class, "store-info__hours-row")]//*[@class="store-info__time"]/text()'
            ).getall(),
        )
        apply_category(Categories.ICE_CREAM, item)
        amenities = response.xpath('//*[@class="store-info__amenity-item"]/span[2]/text()').extract()
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru Hours" in amenities)
        apply_yes_no(Extras.KIDS_AREA, item, "Play Area" in amenities)
        yield item

    def parse_hours(self, days, times) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, time in zip(days, times):
            if time.upper() == "CLOSED":
                opening_hours.set_closed(day)
            else:
                if match := re.findall(r"\d{1,2}:\d{2}(?:am|pm)", time):
                    opening_hours.add_range(day, *match, "%I:%M%p")
        return opening_hours
