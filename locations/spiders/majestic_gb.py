from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class MajesticGBSpider(CrawlSpider):
    name = "majestic_gb"
    item_attributes = {"brand": "Majestic", "brand_wikidata": "Q6737725"}
    start_urls = ["https://www.majestic.co.uk/stores"]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse")]

    def parse(self, response, **kwargs):
        for location in response.xpath('//li[contains(@class, "store-item")]'):
            item = Feature()
            item["ref"] = item["website"] = response.urljoin(location.xpath(".//@data-id").get())
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-long").get()
            item["name"] = location.xpath(".//@data-name").get()
            item["phone"] = location.xpath(".//@data-phone").get()
            item["image"] = location.xpath('./span[@class="store-list-image"]/img/@src').get()

            yield item
