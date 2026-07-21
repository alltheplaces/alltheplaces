from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DELIMITERS_EN, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BataINSpider(SitemapSpider, StructuredDataSpider):
    name = "bata_in"
    BATA = {"brand": "Bata", "brand_wikidata": "Q688082"}
    HUSH_PUPPIES = {"brand": "Hush Puppies", "brand_wikidata": "Q1828588"}
    allowed_domains = ["stores.bata.com"]
    sitemap_urls = ["https://stores.bata.com/sitemap.xml"]
    sitemap_rules = [(r"-store-in-", "parse")]
    search_for_email = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.xpath('//*[contains(text(), "Store Code:")]/text()').re_first(r"Store Code:\s*(\S+)")

        # Coordinates are supplied on the business itself rather than in a "geo" object.
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")
        item["branch"] = item.pop("name", "").removeprefix("Bata in ")
        item["addr_full"] = item.pop("street_address")

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('(//ul[@ref="overflowList"])[1]/li/text()').getall():
            day, _, hours = row.partition(":")
            open_time, _, close_time = hours.strip().partition(" - ")

            # Days appear either as a single day ("Monday") or a range ("Sunday - Saturday").
            days = [day] if sanitise_day(day) else []
            for delimiter in DELIMITERS_EN:
                start, sep, end = day.partition(delimiter)
                if sep and sanitise_day(start) and sanitise_day(end):
                    days = day_range(start, end)
                    break
            try:
                item["opening_hours"].add_days_range(
                    days, open_time.strip(), close_time.strip(), time_format="%I:%M %p"
                )
            except ValueError:
                # Some stores contain malformed hours (e.g. "24:00 AM"); skip those entries.
                continue

        if "hush-puppies" in response.url:
            item.update(self.HUSH_PUPPIES)
        else:
            item.update(self.BATA)
        apply_category(Categories.SHOP_SHOES, item)

        yield item
