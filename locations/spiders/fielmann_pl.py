from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FielmannPLSpider(SitemapSpider, StructuredDataSpider):
    name = "fielmann_pl"
    item_attributes = {"brand": "Fielmann", "brand_wikidata": "Q457822"}
    sitemap_urls = [
        "https://www.fielmann.pl/pl-pl/stores_details01.xml",
    ]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item["phone"] = ld_data["contactPoint"]["telephone"]
        yield item
