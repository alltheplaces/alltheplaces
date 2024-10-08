import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsATSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_at"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.at"]
    sitemap_urls = ["https://www.mcdonalds.at/wso_restaurant-sitemap.xml"]
    download_delay = 0.5

    def parse(self, response):
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["lat"] = response.xpath('//*[@class="marker"]/@data-lat').get()
        item["lon"] = response.xpath('//*[@class="marker"]/@data-lng').get()
        yield item
