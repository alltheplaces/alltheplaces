from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AllianzDESpider(SitemapSpider, StructuredDataSpider):
    name = "allianz_de"
    item_attributes = {"brand": "Allianz", "brand_wikidata": "Q487292"}
    sitemap_urls = [
        "https://vertretung.allianz.de/sitemap.xml",
    ]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["phone"] = ld_data.get("telePhone", None)
        yield item
