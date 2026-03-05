from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CrownBurgersUSSpider(Spider):
    name = "crown_burgers_us"
    item_attributes = {"brand": "Crown Burgers", "name": "Crown Burgers", "brand_wikidata": "Q5189316"}
    allowed_domains = ["crown-burgers.com"]
    start_urls = ["http://www.crown-burgers.com/locations.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="loc_nums"]'):
            item = Feature()
            item["ref"] = item["branch"] = location.xpath("./text()").get("").split("(")[0].strip()
            location_details = location.xpath("./following-sibling::*[1]")
            location_info = location_details.xpath("./text()[normalize-space()]").getall()
            item["addr_full"] = merge_address_lines(location_info[:-1])
            item["phone"] = location_info[-1]
            extract_google_position(item, location_details)
            apply_category(Categories.RESTAURANT, item)
            yield item
