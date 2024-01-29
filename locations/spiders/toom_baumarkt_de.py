from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ToomBaumarktDeSpider(SitemapSpider, StructuredDataSpider):
    name = "toom_baumarkt_de"
    item_attributes = {"brand": "Toom Baumarkt", "brand_wikidata": "Q2442970"}
    sitemap_urls = ["https://static.toom.de/sitemap/cms/newmarkets-0.xml"]
    json_parser = "chompjs"
