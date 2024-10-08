import scrapy

from locations.open_graph_spider import OpenGraphSpider


class PremierGBSpider(scrapy.spiders.SitemapSpider, OpenGraphSpider):
    name = "premier_gb"
    item_attributes = {"brand": "Premier", "brand_wikidata": "Q7240340"}
    allowed_domains = ["premier-stores.co.uk"]
    sitemap_urls = ["https://www.premier-stores.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]

    def post_process_item(self, item, response, **kwargs):
        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        yield item
