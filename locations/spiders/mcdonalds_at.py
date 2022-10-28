import scrapy
from locations.items import GeojsonPointItem
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsATSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_at"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.at"]
    sitemap_urls = ["https://www.mcdonalds.at/wso_restaurant-sitemap.xml"]
    download_delay = 0.5

    def parse(self, response):
        item = GeojsonPointItem()
        item["website"] = item["ref"] = response.url
        item["lat"] = response.xpath('//*[@class="marker"]/@data-lat').get()
        item["lon"] = response.xpath('//*[@class="marker"]/@data-lng').get()
        yield item
