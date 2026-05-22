from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category, Categories
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
    sitemap_rules = [(r"/store-finder/[^/]+/[^/]+/$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.strip("/").split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Forty Winks ")
        item["image"] = None

        # Opening hours in JSON-LD is not the actual values
        # Extract real opening hours directly from the HTML list elements
        oh = OpeningHours()
        if hours_elements := response.xpath("//ul[contains(@class, 'mb-6')]/li"):
            for li in hours_elements:
                day_text = "".join(li.xpath("./div[1]/text()").getall()).strip()
                time_text = "".join(li.xpath("./div[2]/text()").getall()).strip()

                if not day_text or not time_text:
                    continue

                open_t, close_t = time_text.split(" - ")
                oh.add_range(day_text, open_t, close_t, "%I:%M%p")

        item["opening_hours"] = oh

        apply_category(Categories.SHOP_BED, item)

        yield item
