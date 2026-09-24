from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BOT_USER_AGENT_SCRAPY


class PostieNZSpider(CrawlSpider, StructuredDataSpider):
    name = "postie_nz"
    item_attributes = {
        "brand": "Postie",
        "brand_wikidata": "Q110299434",
    }
    start_urls = ["https://www.postie.co.nz/stores/all"]
    custom_settings = {"USER_AGENT": BOT_USER_AGENT_SCRAPY}
    rules = [Rule(LinkExtractor(allow=r"/store-detail/[\w-]+/[\w-]+"), callback="parse")]
    drop_attributes = {"facebook"}

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data["openingHoursText"] = ld_data.pop("openingHours", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Postie ").strip()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(" ".join(ld_data.get("openingHoursText") or []))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
