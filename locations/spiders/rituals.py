from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RitualsSpider(SitemapSpider, StructuredDataSpider):
    name = "rituals"
    item_attributes = {"brand": "Rituals", "brand_wikidata": "Q62874140"}
    sitemap_urls = ["https://www.rituals.com/sitemap.xml"]
    sitemap_rules = [("/store-detail", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rsplit("=", maxsplit=1)[-1]
        item["website"] = response.url
        yield item
