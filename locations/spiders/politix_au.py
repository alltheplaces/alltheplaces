from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PolitixAUSpider(CrawlSpider):
    name = "politix_au"
    item_attributes = {"brand": "Politix", "brand_wikidata": "Q126166036"}
    start_urls = ["https://www.politix.com.au/pages/stores"]
    rules = [Rule(LinkExtractor(r"/pages/stores/[^/]+$"), "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(response.xpath('//*[@class="store-detail__address"]//text()').getall())
        item["phone"] = response.xpath('//*[@class="store-details__phone-text"]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        oh = OpeningHours()
        for hours_text in response.xpath("//tbody//tr"):
            day = hours_text.xpath("normalize-space()").get()
            oh.add_ranges_from_string(day)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
