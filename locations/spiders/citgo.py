import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CitgoSpider(SitemapSpider, StructuredDataSpider):
    name = "citgo"
    item_attributes = {"brand": "Citgo", "brand_wikidata": "Q2974437"}
    allowed_domains = ["citgo.com"]
    sitemap_urls = ["https://www.citgo.com/sitemap.xml"]
    sitemap_rules = [
        (r"/station-locator/locations/(\d+)", "parse_sd"),
    ]
    user_agent = BROWSER_DEFAULT

    def pre_process_data(self, ld_data: dict, **kwargs):
        if opening_hours := ld_data.get("openingHours"):
            ld_data["openingHours"] = re.sub(r"24:00[-\s]+24:00", "00:00-23:59", opening_hours)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name")
        apply_category(Categories.FUEL_STATION, item)

        services = [service.strip() for service in response.xpath('//li[@class="service__item"]/text()').getall()]

        # apply_yes_no(Fuel.OCTANE_87, item, "TOP TIER™ CITGO TriCLEAN® Gasoline" in services)
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in services)
        apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in services)
        apply_yes_no(Fuel.ETHANOL_FREE, item, "Ethanol Free" in services)
        apply_yes_no(Fuel.E85, item, "E85" in services)
        apply_yes_no(Access.HGV, item, "Truck Stop" in services)
        apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in services)
        yield item
