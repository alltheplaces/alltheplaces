from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ToomBaumarktDESpider(SitemapSpider, StructuredDataSpider):
    name = "toom_baumarkt_de"
    item_attributes = {"brand": "toom Baumarkt", "brand_wikidata": "Q2442970"}
    sitemap_urls = ["https://static.toom.de/sitemap/cms.xml"]
    sitemap_follow = ["newmarkets"]
    json_parser = "chompjs"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").split(" in ", 1)[1]

        yield item
