import scrapy

from locations.open_graph_parser import OpenGraphParser


class PremierGBSpider(scrapy.spiders.SitemapSpider):
    name = "premier_gb"
    item_attributes = {"brand": "Premier", "brand_wikidata": "Q7240340"}
    allowed_domains = ["premier-stores.co.uk"]
    sitemap_urls = ["https://www.premier-stores.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse_store")]

    def parse_store(self, response):
        item = OpenGraphParser.parse(response)

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        yield item
