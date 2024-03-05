from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class WalgreensSpider(SitemapSpider, StructuredDataSpider):
    name = "walgreens"
    WALGREENS = {"brand": "Walgreens", "brand_wikidata": "Q1591889"}
    DUANE_READE = {"brand": "Duane Reade", "brand_wikidata": "Q5310380"}
    sitemap_urls = ["https://www.walgreens.com/sitemap-storedetails.xml"]
    sitemap_rules = [("", "parse_sd")]
    download_delay = 2.0

    def pre_process_data(self, ld_data, **kwargs):
        # Tue Jan 10 -> Tu
        for rule in ld_data.get("openingHoursSpecification"):
            if len(rule["dayOfWeek"]) > 2:
                rule["dayOfWeek"] = rule["dayOfWeek"][:2]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "/locator/walgreens-" in response.url:
            item.update(self.WALGREENS)
        elif item["name"] == "Duane Reade":
            item.update(self.DUANE_READE)
        # TODO: a few more brands here

        apply_category(Categories.PHARMACY, item)
        yield item
