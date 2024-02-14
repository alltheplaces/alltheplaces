from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FielmannCHSpider(SitemapSpider, StructuredDataSpider):
    name = "fielmann_ch"
    item_attributes = {"brand": "Fielmann", "brand_wikidata": "Q457822"}
    sitemap_urls = [
        "https://www.fielmann.ch/de-ch/stores_details01.xml",
    ]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item["phone"] = ld_data["contactPoint"]["telephone"]
        yield item
