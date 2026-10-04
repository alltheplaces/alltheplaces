import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SantaFeCattleCOUSSpider(Spider):
    name = "santa_fe_cattle_co_us"
    item_attributes = {"brand": "Santa Fe Cattle Co."}
    start_urls = ["https://www.santafecattle.com/"]

    def parse(self, response: Response) -> Iterable[Request]:
        for url in response.css("a::attr(href)").getall():
            if re.search(r"santafecattle\.com/[a-z-]+-(?:al|ok|la|ms|tn)/?$", url):
                yield response.follow(url, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        paragraphs = response.css('[data-testid="richTextElement"] p')
        lines = [text.strip() for text in paragraphs.xpath(".//text()").getall() if text.strip()]
        for index, line in enumerate(lines):
            if match := re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5})", line):
                city, state, postcode = match.groups()
                item = Feature(
                    ref=response.url.rstrip("/").rsplit("/", 1)[-1],
                    street_address=lines[index - 1],
                    city=city,
                    state=state,
                    postcode=postcode,
                    country="US",
                    phone=lines[index + 1],
                    website=response.url,
                )
                break
        else:
            return

        hours = OpeningHours()
        for paragraph in paragraphs:
            line = paragraph.xpath("normalize-space(.)").get()
            if re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", line):
                hours.add_ranges_from_string(line)
        item["opening_hours"] = hours
        apply_category(Categories.RESTAURANT, item)
        yield item
