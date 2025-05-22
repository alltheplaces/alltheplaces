import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class FarmersHomeFurnitureUSSpider(SitemapSpider):
    name = "farmers_home_furniture_us"
    item_attributes = {
        "brand": "Farmers Home Furniture",
        "brand_wikidata": "Q121586393",
        "country": "US",
    }
    allowed_domains = ["www.farmershomefurniture.com"]
    sitemap_urls = ["https://www.farmershomefurniture.com/sitemaps/sitemap_stores.xml"]
    sitemap_rules = [("/stores/", "parse")]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    coordinates_pattern = re.compile(r"position: {lat:\s*([-\d.]+)[,\s]+lng:\s*([-\d.]+)}")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//*[contains(@id,"address")]/span/text()').getall())
        if coordinates := re.search(self.coordinates_pattern, response.text):
            item["lat"], item["lon"] = coordinates.groups()
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get("")
        yield item
