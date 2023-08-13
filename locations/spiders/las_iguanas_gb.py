from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import extract_email, extract_phone


class LasIguanasGBSpider(SitemapSpider):
    name = "las_iguanas_gb"
    item_attributes = {"brand": "Las Iguanas", "brand_wikidata": "Q19875012"}
    sitemap_urls = ["https://www.iguanas.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[-\w]+/[-\w]+$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//div[@class="address"]/text()').get())
        item["extras"]["branch"] = response.xpath('//h1[@class="restaurant-title"]/text()').get()
        extract_google_position(item, response)
        extract_email(item, response)
        extract_phone(item, response)

        yield item
