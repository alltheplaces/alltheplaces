from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PipoosNLSpider(CrawlSpider, StructuredDataSpider):
    name = "pipoos_nl"
    item_attributes = {"brand": "pipoos", "brand_wikidata": "Q106581278"}
    start_urls = ["https://pipoos.com/winkels/"]
    rules = [Rule(LinkExtractor(allow=r"/winkels/pipoos-"), callback="parse_sd")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # Remove brand prefix from name to set branch
        name = item.pop("name", "") or ""
        item["branch"] = name.removeprefix("pipoos ").strip()

        # Drop placeholder image (no actual per-location image path)
        if item.get("image") and item["image"].rstrip("/").endswith("/image"):
            item.pop("image")

        apply_category(Categories.SHOP_CRAFT, item)
        yield item
