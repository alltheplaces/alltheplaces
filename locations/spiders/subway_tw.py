from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class SubwayTWSpider(CrawlSpider):
    name = "subway_tw"
    item_attributes = {"brand": "Subway", "brand_wikidata": "Q244457"}
    start_urls = ["https://subway.com.tw/en/include/index.php#newStore"]
    rules = [
        Rule(LinkExtractor(allow=r"pageNum"), callback="parse", follow=True),
    ]

    def parse(self, response, **kwargs):
        for store in response.xpath("//*[contains(@class, 'store-table')]/tbody/tr"):
            item = Feature()
            item["name"] = store.xpath('./*[@data-title="Location"]/text()').get().strip()
            item["addr_full"] = store.xpath('./*[@data-title="Address"]/a/text()').get().replace("\n", "")
            item["phone"] = store.xpath('.//a[contains(@href, "tel")]/@href').get()
            item["ref"] = store.xpath('./*[@data-title="NO"]/text()').get().strip()
            item["website"] = response.url
            yield item
