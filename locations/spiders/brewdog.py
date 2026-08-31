from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class BrewdogSpider(SitemapSpider):
    name = "brewdog"
    item_attributes = {"brand": "BrewDog", "brand_wikidata": "Q911367"}
    sitemap_urls = ["https://brewdog.com/sitemap.xml", "https://usa.brewdog.com/sitemap.xml"]
    sitemap_rules = [("/pages/bars/", "parse")]

    def parse(self, response):
        item = Feature()
        item["branch"] = response.xpath('//*[@class="bar-detail-hero__title"]//text()').get()
        item["addr_full"] = response.xpath('//*[@class="bar-detail-hero__address"]//text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
