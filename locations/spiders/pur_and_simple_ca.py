from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class PurAndSimpleCASpider(SitemapSpider):
    name = "pur_and_simple_ca"
    item_attributes = {"brand": "Pür & Simple", "brand_wikidata": "Q118558630"}
    sitemap_urls = ["https://pursimple.com/sitemap_index.xml"]
    sitemap_rules = [(r"https://pursimple.com/restaurant/[^/]+/$", "parse")]

    def parse(self, response, **kwargs):
        if address := response.xpath('//*[@class="location-address-content"]//*[@class="p_lead"]/text()').get():
            item = Feature()
            item["branch"] = response.xpath("//h1//text()").get()
            item["addr_full"] = address
            item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
            item["website"] = item["ref"] = response.url
            extract_google_position(item, response)
            yield item
