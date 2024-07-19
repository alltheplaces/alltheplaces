from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class OdidoPLSpider(SitemapSpider):
    name = "odido_pl"
    item_attributes = {"brand": "Odido", "brand_wikidata": "Q106947294"}
    sitemap_urls = ["https://www.sklepy-odido.pl/sitemap.xml"]
    sitemap_rules = [("-sklep/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["name"] = response.xpath('//*[@class="store-name field-store-name"]/text()').get()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[@class="store-address"]/text()').get()
        extract_google_position(item, response)
        yield item
