from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class JohnDorysZASpider(CrawlSpider, StructuredDataSpider):
    name = "john_dorys_za"
    item_attributes = {"brand": "John Dory's", "brand_wikidata": "Q130140080", "extras": Categories.RESTAURANT.value}
    start_urls = ["https://www.johndorys.com/za/find-a-restaurant/?ParentId=1300&Results=true"]
    allowed_domains = ["johndorys.com", "johndorys.co.za"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.johndorys.com/za/find-a-restaurant/.+"), callback="parse_sd", follow=True
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["website"] = response.url  # SD has outdated url for at least some locations
        item.pop("image", None)
        if "JohnDorysSA" in item.get("facebook"):
            item.pop("facebook")
        if "johndoryssa" in item.get("twitter"):
            item.pop("twitter")
        yield item
