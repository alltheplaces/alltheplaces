from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class LasIguanasGBSpider(SitemapSpider):
    name = "las_iguanas_gb"
    item_attributes = {"brand": "Las Iguanas", "brand_wikidata": "Q19875012"}
    sitemap_urls = ["https://www.iguanas.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[^/]+/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1/span/text()").get()
        item["addr_full"] = (
            response.xpath('//*[@class="contact-info"]//*[@class="my-4"]//p').xpath("normalize-space()").get()
        )
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/span/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
