from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FreewayInsuranceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "freeway_insurance_us"
    item_attributes = {"brand": "Freeway Insurance", "brand_wikidata": "Q108044578"}
    sitemap_urls = [
        "https://locations.freeway.com/sitemap.xml",
    ]
    wanted_types = ["InsuranceAgency"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
