from typing import Any, Iterable

from scrapy.http import HtmlResponse, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

# Store pages are listed in the site's own US store sitemap and carry a
# schema.org ToyStore record with address, coordinates, phone and hours.
#
# The chain is also served by a Salesforce Commerce Cloud endpoint that returns
# every store in one response, but robots.txt disallows /on/demandware.store*,
# so the sitemap is used instead. Note that the sitemap lists fewer stores than
# that endpoint reports, and that some of the pages it does list are closed
# stores.


class BuildABearWorkshopUSSpider(SitemapSpider, StructuredDataSpider):
    name = "build_a_bear_workshop_us"
    item_attributes = {"brand": "Build-A-Bear Workshop", "brand_wikidata": "Q1002992"}
    allowed_domains = ["www.buildabear.com"]
    # Akamai answers 403 to requests from outside the US.
    requires_proxy = True
    # Akamai bans the project user agent even through the proxy, so the
    # proxy is left to choose one.
    custom_settings = {"USER_AGENT": None}
    sitemap_urls = ["https://www.buildabear.com/sitemap-usstores.xml"]
    sitemap_rules = [(r"/locations\?StoreID=(\d+)", "parse_store")]
    wanted_types = ["ToyStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # Closed stores are served as image/jpeg, which scrapy does not parse as
        # HTML, so they are skipped rather than raising.
        if not isinstance(response, HtmlResponse):
            return
        yield from self.parse_sd(response)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # "Build-A-Bear Workshop at Roosevelt Field, Garden City, NY"
        item["branch"] = (item.pop("name", None) or "").removeprefix("Build-A-Bear Workshop at ").rsplit(", ", 2)[0]
        # The same brand placeholder is used on every page.
        item["image"] = None

        # "Mo-Sa 10:00am-9:00pm, Su 11:00am-6:00pm", which the linked data
        # parser does not read.
        if opening_hours := ld_data.get("openingHours"):
            oh = OpeningHours()
            oh.add_ranges_from_string(opening_hours)
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_TOYS, item)

        yield item
