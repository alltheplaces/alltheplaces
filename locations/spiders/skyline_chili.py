from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SkylineChiliSpider(SitemapSpider, StructuredDataSpider):
    name = "skyline_chili"
    item_attributes = {
        "name": "Skyline Chili",
        "brand": "Skyline Chili",
        "brand_wikidata": "Q151224",
    }

    sitemap_urls = ["https://locations.skylinechili.com/sitemap.xml"]
