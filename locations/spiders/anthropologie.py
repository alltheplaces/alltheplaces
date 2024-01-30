from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class AnthropologieSpider(SitemapSpider, StructuredDataSpider):
    name = "anthropologie"
    item_attributes = {"brand": "Anthropologie", "brand_wikidata": "Q4773903"}
    allowed_domains = ["anthropologie.com"]
    sitemap_urls = ["https://www.anthropologie.com/store_sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    requires_proxy = True

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["geo"]["latitude"], ld_data["geo"]["longitude"] = (
            ld_data["geo"]["longitude"],
            ld_data["geo"]["latitude"],
        )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix(" - Anthropologie Store")

        if item["branch"].startswith("Closed - ") or item["branch"].endswith(" - Closed"):
            set_closed(item)

        yield item
