from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class FortyWinksAUSpider(SitemapSpider, PlaywrightSpider, StructuredDataSpider):
    name = "forty_winks_au"
    item_attributes = {"brand": "Forty Winks", "brand_wikidata": "Q106283438"}
    allowed_domains = ["www.fortywinks.com.au"]
    sitemap_urls = ["https://www.fortywinks.com.au/sitemap.xml"]
    sitemap_rules = [(r"/store-finder/", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.strip("/").split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Forty Winks ")

        # Opening hours in JSON-LD is not the actual values
        item["opening_hours"] = None

        # Extract real opening hours directly from the HTML list elements
        if hours_elements := response.xpath("//ul[contains(@class, 'mb-6')]/li"):
            oh = OpeningHours()
            for li in hours_elements:
                day_text = "".join(li.xpath("./div[1]/text()").getall()).strip()
                time_text = "".join(li.xpath("./div[2]/text()").getall()).strip()

                if not day_text or not time_text or "closed" in time_text.lower():
                    continue

                open_t, close_t = time_text.split("-")
                oh.add_range(day=day_text, open_time=open_t.strip(), close_time=close_t.strip(), time_format="%I:%M%p")

            if oh:
                item["opening_hours"] = oh

        item["image"] = item["facebook"] = None

        yield item
