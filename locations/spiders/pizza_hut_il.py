from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IL, OpeningHours
from locations.items import Feature


class PizzaHutILSpider(CrawlSpider):
    name = "pizza_hut_il"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://www.pizzahut.co.il/branch/"]
    rules = [Rule(LinkExtractor(allow=r"https://www.pizzahut.co.il/branch/.*"), callback="parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["name"] = response.xpath(r"//title/text()").get().replace("|", "-")
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath(r'//*[@data-id = "e7f56e4"]//li[3]/span[2]/text()').get()
        item["phone"] = response.xpath(r'//*[@data-id = "e7f56e4"]//li[2]').xpath("normalize-space()").get()
        oh = OpeningHours()
        if m := response.xpath(r'//*[@class="elementor-icon-list-items make_date"]'):
            for day_time in m.xpath(".//li/span[2]"):
                oh.add_ranges_from_string(day_time.xpath("./text()").get(), days=DAYS_IL)
                item["opening_hours"] = oh
        apply_category(Categories.RESTAURANT, item)

        yield item
