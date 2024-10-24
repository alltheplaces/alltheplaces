from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.sport_master_dk import SportMasterDKSpider
from locations.structured_data_spider import StructuredDataSpider


class SportsDirectSpider(CrawlSpider, StructuredDataSpider):
    name = "sports_direct"
    SPORTS_DIRECT = {"brand": "Sports Direct", "brand_wikidata": "Q7579661"}
    start_urls = ["https://www.sportsdirect.com/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"store\-([\d]+)$"), callback="parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("Sportmaster "):
            item.update(SportMasterDKSpider.item_attributes)
            item["branch"] = item.pop("name").removeprefix("Sportmaster ")
        elif item["name"].startswith("Field & Trek "):
            item.update(SportMasterDKSpider.item_attributes)
            item["branch"] = item.pop("name").removeprefix("Field & Trek ")
            item["name"] = item["brand"] = "Field & Trek"
            apply_category(Categories.SHOP_SPORTS, item)
        else:
            item["branch"] = item.pop("name").removeprefix("Sports Direct ")
            item.update(self.SPORTS_DIRECT)

        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        item["street_address"] = merge_address_lines(
            response.xpath('//*[@itemprop="address"]/following-sibling::div[1]/text()').getall()
        )
        item["addr_full"] = merge_address_lines(
            response.xpath('//*[@itemprop="address"]/following-sibling::div/text()').getall()
        )
        yield item
