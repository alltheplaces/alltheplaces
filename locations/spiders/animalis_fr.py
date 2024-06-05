from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AnimalisFRSpider(SitemapSpider, StructuredDataSpider):
    name = "animalis_fr"
    item_attributes = {"brand": "Animalis", "brand_wikidata": "Q2850015"}
    sitemap_urls = ["https://magasin.animalis.com/locationsitemap1.xml"]
