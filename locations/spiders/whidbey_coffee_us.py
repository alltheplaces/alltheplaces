import re
from datetime import datetime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class WhidbeyCoffeeUSSpider(SitemapSpider):
    name = "whidbey_coffee_us"
    item_attributes = {"brand": "Whidbey Coffee"}
    allowed_domains = ["www.whidbeycoffee.com"]
    sitemap_urls = ("https://www.whidbeycoffee.com/sitemap.xml",)
    sitemap_rules = [(r"/pages/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_block = response.xpath('//p[strong[contains(text(), "Location") or contains(text(), "Address")]]')
        if not location_block:
            return

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//h1/text()").get("").strip()

        iframe_src = response.xpath('//iframe[contains(@src, "maps")]/@src').get("")
        if m := re.search(r"!3d(-?[\d.]+).*!2d(-?[\d.]+)|!2d(-?[\d.]+).*!3d(-?[\d.]+)", iframe_src):
            lat3, lon2, lon2b, lat3b = m.groups()
            item["lat"] = lat3 or lat3b
            item["lon"] = lon2 or lon2b
        elif m := re.search(r"/@(-?[\d.]+),(-?[\d.]+)", response.text):
            item["lat"], item["lon"] = m.groups()

        address_lines = [t.strip() for t in location_block.xpath(".//a//text()").getall() if t.strip()]
        if address_lines:
            item["addr_full"] = ", ".join(address_lines)

        phone_block = response.xpath('//p[strong[contains(text(), "Phone")]]')
        if phone_block:
            phone_text = " ".join(t.strip() for t in phone_block.xpath(".//text()").getall() if t.strip())
            item["phone"] = re.sub(r"(?i)^phone:?\s*", "", phone_text).strip()

        hours_text = response.xpath('//p[strong[contains(text(), "Hours")]]//text()').getall()
        if hours_text:
            item["opening_hours"] = self.parse_hours(hours_text)

        apply_category(Categories.COFFEE_SHOP, item)
        yield item

    def parse_hours(self, hours: list) -> OpeningHours:
        opening_hours = OpeningHours()
        for hour in hours:
            if "-" not in hour:
                continue
            if "Drive Thru" in hour or "Cafe" in hour:
                continue
            day_range = hour.split(" ")[0]
            time_range = "".join(hour.split(" ")[1:])
            open_time, close_time = time_range.strip().split("-")
            if ":" not in open_time:
                open_time = datetime.strptime(open_time, "%I%p").strftime("%I:%M%p")
            if ":" not in close_time:
                close_time = datetime.strptime(close_time, "%I%p").strftime("%I:%M%p")
            if "-" in day_range:
                start_day, end_day = re.sub(r"[\s:]", "", day_range).split("-")
                for day in DAYS_3_LETTERS_FROM_SUNDAY[
                    DAYS_3_LETTERS_FROM_SUNDAY.index(start_day[0:3]) : DAYS_3_LETTERS_FROM_SUNDAY.index(end_day[0:3])
                    + 1
                ]:
                    opening_hours.add_range(
                        day=day[0:2],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%I:%M%p",
                    )
            else:
                opening_hours.add_range(
                    day=day_range[0:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )
        return opening_hours
