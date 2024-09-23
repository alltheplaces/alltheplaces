from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class MaxboNOSpider(SitemapSpider):
    name = "maxbo_no"
    item_attributes = {"brand": "Maxbo", "brand_wikidata": "Q11988771"}
    sitemap_urls = ["https://www.maxbo.no/sitemap.xml"]
    sitemap_rules = [("/butikker/", "parse")]

    def parse(self, response):
        item = Feature()
        item["name"] = response.xpath("//title/text()").get().replace("|", "-")
        item["addr_full"] = response.xpath('//*[contains(@href,"maps/search/")]').xpath("normalize-space()").get()
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        yield item
