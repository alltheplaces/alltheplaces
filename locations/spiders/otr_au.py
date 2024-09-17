from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.items import Feature


class OtrAUSpider(SitemapSpider):
    name = "otr_au"
    item_attributes = {"brand": "OTR", "brand_wikidata": "Q116394019", "extras": Categories.FUEL_STATION.value}
    sitemap_urls = ["https://www.otr.com.au/robots.txt"]
    sitemap_rules = [("/location/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath("//title/text()").get()
        item["addr_full"] = response.xpath("//iframe/@title").get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        extract_google_position(item, response)
        yield item
