import scrapy
from locations.brands import Brand
from locations.seo import extract_html_meta_details, has_geo


class LondisSpider(scrapy.spiders.SitemapSpider):

    name = "londis"
    allowed_domains = ['londis.co.uk']
    sitemap_urls = ['https://www.londis.co.uk/sitemap.xml']
    sitemap_rules = [('/our-stores/', 'parse_store')]

    def parse_store(self, response):
        item = Brand.LONDIS.item(response)
        if has_geo(extract_html_meta_details(item, response)):
            yield item
