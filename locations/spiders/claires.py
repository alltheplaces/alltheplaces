from scrapy.spiders import SitemapSpider

from locations.spiders.pandora import PandoraSpider


class ClairesSpider(SitemapSpider):
    name = "claires"
    item_attributes = {"brand": "Claire's", "brand_wikidata": "Q2974996"}
    allowed_domains = ["claires.com"]
    sitemap_urls = ["https://stores.claires.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.claires\.com\/.+\/([-\w]+\/\d+)\.html$",
            "parse_store",
        )
    ]
    download_delay = 0.2
    requires_proxy = True

    def parse_store(self, response):
        yield PandoraSpider.parse_item(response, self.sitemap_rules[0][0])
