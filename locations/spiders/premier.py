import scrapy
from locations.brands import Brand
from locations.seo import extract_html_meta_details, has_geo


class PremierSpider(scrapy.spiders.SitemapSpider):

    name = "premier"
    allowed_domains = ['premier-stores.co.uk']
    sitemap_urls = ['https://www.premier-stores.co.uk/sitemap.xml']
    sitemap_rules = [('/our-stores/', 'parse_store')]

    def parse_store(self, response):
        item = Brand.PREMIER_STORES.item(response)
        if has_geo(extract_html_meta_details(item, response)):
            yield item
