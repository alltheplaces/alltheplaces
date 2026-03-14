from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MyEyeDrSpider(SitemapSpider, StructuredDataSpider):
    name = "my_eye_dr"
    item_attributes = {"brand": "MyEyeDr.", "brand_wikidata": "Q117864710"}
    sitemap_urls = [
        "https://locations.myeyedr.com/sitemap1.xml",
    ]
