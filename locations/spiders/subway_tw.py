from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.subway import SubwaySpider


class SubwayTWSpider(CrawlSpider):
    name = "subway_tw"
    item_attributes = SubwaySpider.item_attributes
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
            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "sandwich"
            item["extras"]["takeaway"] = "yes"
            yield item
