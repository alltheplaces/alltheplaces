from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PremierurgentcareSpider(SitemapSpider, StructuredDataSpider):
    name = "premierurgentcare"
    item_attributes = {"brand": "Premier Urgent Care"}
    allowed_domains = ["www.premier.care"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    sitemap_urls = ["https://www.premier.care/sitemap.xml"]
    # Example:     # https://www.premier.care/locations/thumbs-up-temple/
    sitemap_rules = [(r"/locations/[\w-]+/$", "parse_sd")]
    wanted_types = ["MedicalOrganization"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.CLINIC, item)
        apply_yes_no("emergency", item, True)
        yield item
