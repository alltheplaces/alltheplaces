from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OrkinUSSpider(SitemapSpider, StructuredDataSpider):
    name = "orkin_us"
    item_attributes = {"brand": "Orkin", "brand_wikidata": "Q7102943"}
    sitemap_urls = ["https://www.orkin.com/robots.txt"]
    sitemap_rules = [("/branch-", "parse")]

    def pre_process_data(self, ld_data, **kwargs):
        # Opening hours seem suspect
        # ld_data["openingHoursSpecification"] = [ld_data["openingHoursSpecification"]]
        ld_data["openingHoursSpecification"] = None
