from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GreatWolfResortsUSSpider(SitemapSpider):
    name = "great_wolf_resorts_us"
    item_attributes = {"name": "Great Wolf Lodge", "brand": "Great Wolf Lodge", "brand_wikidata": "Q5600260"}
    allowed_domains = ["www.greatwolf.com"]
    sitemap_urls = ["https://www.greatwolf.com/php-root.sitemap.xml"]
    sitemap_rules = [(r"/customer-service$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@property="og:site_name"]/@content').get()
        item["street_address"] = response.xpath('//*[@class="cmp-text__content"]//p/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="cmp-text__content"]//p//text()').get()]
        )
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        apply_category({"leisure": "water_park"}, item)
        yield item

    # def post_process_item(self, item: Any, response: Response, ld_data: dict, **kwargs: Any) -> Any:
    #     item.pop("facebook")
    #     item.pop("twitter")
    #     item["branch"] = item.pop("name").removeprefix("Great Wolf Lodge ")
    #
    #     apply_category({"leisure": "water_park"}, item)
    #     yield item
