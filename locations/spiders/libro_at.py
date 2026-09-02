from typing import Iterable

from scrapy import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class LibroATSpider(CrawlSpider, StructuredDataSpider):
    name = "libro_at"
    item_attributes = {"brand": "Libro", "brand_wikidata": "Q1823138"}
    requires_proxy = True
    brands = {
        "libro": {"brand": "Libro", "brand_wikidata": "Q1823138"},
        "pagro": {"brand": "Pagro", "brand_wikidata": "Q57550022"},
    }
    start_urls = ["https://www.pagro.at/filialfinder"]
    rules = [
        Rule(
            LinkExtractor(
                allow="/filialfinder/",
            ),
            callback="parse_sd",
        ),
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["name"], item["addr_full"] = item.pop("name").split(" Filiale ", 1)
        item.update(self.brands[item["name"].lower()])
        yield item
