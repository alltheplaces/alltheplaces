from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SubwaySpider(SitemapSpider, StructuredDataSpider):
    """Also see SubwayWorldwideSpider for API-based spider."""

    name = "subway"
    item_attributes = {"brand": "Subway", "brand_wikidata": "Q244457"}
    allowed_domains = ["restaurants.subway.com"]
    sitemap_urls = ["https://restaurants.subway.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data, **kwargs):
        if isinstance(ld_data["name"], list):
            # We actually want the second name in the Microdata
            ld_data["name"] = ld_data["name"][-1]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["takeaway"] = "yes"
        yield item
