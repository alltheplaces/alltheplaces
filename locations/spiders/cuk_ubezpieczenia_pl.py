from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CUKUbezpieczeniaPLSpider(SitemapSpider, StructuredDataSpider):
    name = "cuk_ubezpieczenia_pl"
    item_attributes = {"brand": "CUK Ubezpieczenia", "brand_wikidata": "Q113230028"}
    sitemap_urls = [
        "https://cuk.pl/sitemap.offices.xml",
    ]
    sitemap_rules = [("/placowki/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item["name"].replace("CUK Ubezpieczenia - ", "")
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
