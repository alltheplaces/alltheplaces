import scrapy
from scrapy.spiders.sitemap import SitemapSpider

from locations.storefinders.wp_go_maps import WpGoMapsSpider


class TacototeSpider(SitemapSpider, WpGoMapsSpider):
    name = "tacotote"
    item_attributes = {"brand": "Tacotote", "brand_wikidata": "Q16992316"}
    allowed_domains = ["tacotote.com"]
    sitemap_urls = ["https://tacotote.com/wp-sitemap-posts-page-1.xml"]
    sitemap_rules = [(r"/locations-old/.*$", "parse_city")]

    def parse_city(self, response):
        mapid = response.xpath("//@mapid").extract_first()
        yield scrapy.Request(self.features_url_for(mapid), callback=self.parse_stores)
