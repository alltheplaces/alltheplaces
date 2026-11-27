import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class TatteBakeryAndCafeUSSpider(SitemapSpider):
    name = "tatte_bakery_and_cafe_us"
    item_attributes = {"brand": "Tatte Bakery & Cafe", "brand_wikidata": "Q116671479"}
    allowed_domains = ["tattebakery.com"]
    sitemap_urls = ["https://tattebakery.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[a-z]{2}/[^/]+/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.removeprefix("https://tattebakery.com/locations/").removesuffix("/")
        item["website"] = response.url
        item["branch"] = response.css("h1::text").get()

        address = response.css('a[href*="google.com/maps"]::text').get().strip()
        street, city, state, postcode = re.match(r"^(.*), ([^,]+), ([A-Z]{2}), (\d{5})$", address).groups()
        item["street_address"] = street
        item["city"] = city
        item["state"] = state
        item["postcode"] = postcode

        item["phone"] = response.css('a[href^="tel:"]::attr(href)').get()

        coords = re.search(r"loc:\{.{0,600}?lat:(-?[\d.]+),lng:(-?[\d.]+)", response.text, re.DOTALL)
        item["lat"] = coords.group(1)
        item["lon"] = coords.group(2)

        oh = OpeningHours()
        rows = []
        for row in response.css(".location-hours > div"):
            if day := row.xpath('.//p[contains(@class, "--day")]/text()').get():
                if hours := row.xpath('.//p[contains(@class, "--hours")]/text()').get():
                    rows.append(f"{day} {hours}")
        oh.add_ranges_from_string(" ".join(rows), days=DAYS_EN)
        item["opening_hours"] = oh

        apply_category(Categories.CAFE, item)

        yield item
