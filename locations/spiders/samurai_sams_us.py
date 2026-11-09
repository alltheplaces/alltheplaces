import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


class SamuraiSamsUSSpider(SitemapSpider):
    name = "samurai_sams_us"
    item_attributes = {"brand": "Samurai Sam's Teriyaki Grill"}
    allowed_domains = ["www.samuraisams.net"]
    sitemap_urls = ["https://www.samuraisams.net/sitemap.xml"]
    sitemap_rules = [(r"/stores/(\d+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        address = response.xpath("//address/span/text()").getall()
        if len(address) < 4:
            return

        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[-1]
        item["street_address"] = address[0].strip().rstrip(",")
        item["city"] = address[1].strip()
        item["state"] = address[2].strip()
        item["postcode"] = address[3].strip()
        # The second number on the page is a catering hotline.
        item["phone"] = response.xpath('(//a[@class="phone"])[1]/text()').get()
        item["website"] = response.url

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "japanese;teriyaki"

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        """Parses rows such as "Mon 10:00AM - 5:00PM" and "Sat Closed - Closed"."""
        oh = OpeningHours()

        for row in response.xpath('//div[@class="dineInHours"]//li/text()').getall():
            if not (
                match := re.match(
                    r"(\w{3})\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)",
                    row.strip(),
                    re.I,
                )
            ):
                continue

            day, open_time, close_time = match.groups()
            if day.title() not in DAYS_3_LETTERS:
                continue

            oh.add_range(
                day.title(),
                open_time.replace(" ", "").upper(),
                close_time.replace(" ", "").upper(),
                time_format="%I:%M%p",
            )

        return oh if oh.as_opening_hours() else None
