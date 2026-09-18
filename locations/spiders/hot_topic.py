import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# Store pages come from the site's own store sitemap. The chain is also served
# by a Salesforce Commerce Cloud endpoint in one response, but robots.txt
# disallows */demandware.store*, so the per store pages are used instead.
#
# Each page holds the address as a run of text, the coordinates inside the
# map's data-locations attribute, and the hours as day and time spans.


class HotTopicSpider(SitemapSpider):
    name = "hot_topic"
    item_attributes = {"brand": "Hot Topic", "brand_wikidata": "Q9294032"}
    allowed_domains = ["www.hottopic.com"]
    sitemap_urls = ["https://www.hottopic.com/sitemap-ht-stores-sitemap-0.xml"]
    sitemap_rules = [(r"/store-details\?StoreId=(\d+)", "parse")]
    # Closed stores stay in the sitemap and answer 500, which is not worth
    # retrying.
    custom_settings = {"RETRY_HTTP_CODES": [408, 429, 502, 503, 504]}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The block is a run of text: the street on its own node, then the
        # city, state, postcode and country together on the last one.
        nodes = [
            re.sub(r"\s+", " ", node).strip()
            for node in response.xpath('//div[contains(@class, "store-address")]//text()').getall()
            if node.strip() and node.strip() != ","
        ]
        if not nodes or not (
            locality := re.search(r"(.+?)\s*,\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?\s+([A-Z]{2})$", nodes[-1])
        ):
            return

        item = Feature()
        item["ref"] = response.url.rsplit("=", 1)[-1]
        item["branch"] = response.xpath("//h1/text()").get("").strip()
        item["street_address"] = merge_address_lines(nodes[:-1])
        item["city"], item["state"], item["postcode"], item["country"] = locality.groups()
        item["phone"] = response.xpath('//a[contains(@class, "storelocator-phone")]/text()').get()
        item["website"] = response.url

        if coordinates := re.search(
            r"daddr=(-?\d+\.\d+),(-?\d+\.\d+)", response.xpath('//a[contains(@class, "store-map")]/@href').get("")
        ):
            item["lat"], item["lon"] = coordinates.groups()

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        """Parses rows such as "Mon - Sat" / "11:00AM - 7:00PM"."""
        oh = OpeningHours()

        for row in response.xpath('//div[contains(@class, "hours-row")]'):
            days = (row.xpath('.//span[contains(@class, "store-hours-day")]/text()').get() or "").strip()
            times = (row.xpath('.//span[contains(@class, "store-hours-time")]/text()').get() or "").strip()
            if not (match := re.fullmatch(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", times, re.I)):
                continue

            day_names = []
            for token in re.split(r"&|,|\band\b", days):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if day_names:
                oh.add_days_range(
                    day_names,
                    match.group(1).replace(" ", "").upper(),
                    match.group(2).replace(" ", "").upper(),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None
