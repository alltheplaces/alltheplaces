from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class RitasItalianIceSpider(SitemapSpider):
    name = "ritas_italian_ice"
    item_attributes = {"brand": "Rita's Italian Ice", "brand_wikidata": "Q7336456"}
    allowed_domains = ["ritasice.com"]

    sitemap_urls = ["https://www.ritasice.com/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/location/([^/]+)/$", "parse_store")]

    def parse_store(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//*[@class="wpsl-store-location"]/h2/text()').get()
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/text()').get()
        extract_google_position(item, response)
        yield item
