import html
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FormulaOneAutocentresGBSpider(CrawlSpider, StructuredDataSpider):
    name = "formula_one_autocentres_gb"
    item_attributes = {"brand": "Formula One Autocentres", "brand_wikidata": "Q79239635"}
    start_urls = ["https://www.f1autocentres.co.uk/find-a-centre"]
    rules = [Rule(LinkExtractor(allow=r"/branch/"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = item["ref"] = response.url
        item["image"] = None

        item["branch"] = html.unescape(item.pop("name").removeprefix("Formula One Autocentres "))

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//table[@class="opening-times-table"]/tbody/tr'):
            day, start_time, end_time = rule.xpath("./td/text()").getall()
            item["opening_hours"].add_range(day, start_time, end_time, "%I:%M%p")

        services = response.xpath('//div[@class="services"]//div[@class="columns"]/text()').getall()

        apply_yes_no(Extras.VEHICLE_AIR_CONDITIONING_SERVICES, item, "Air Conditioning" in services)
        apply_yes_no(Extras.VEHICLE_BATTERY_SERVICES, item, "Batteries" in services)
        apply_yes_no(Extras.VEHICLE_BRAKE_SERVICES, item, "Brakes" in services)
        apply_yes_no(Extras.VEHICLE_TYRE_SERVICES, item, "Car Tyres" in services)
        apply_yes_no(Extras.VEHICLE_CLUTCH_SERVICES, item, "Clutches" in services)
        apply_yes_no(Extras.VEHICLE_EXHAUST_SERVICES, item, "Exhausts" in services)
        apply_yes_no(Extras.VEHICLE_INSPECTION_SERVICES, item, "MOT" in services)
        apply_yes_no(Extras.VEHICLE_TYRE_REPAIR_SERVICES, item, "Puncture Repair" in services)
        apply_yes_no(Extras.VEHICLE_PLANNED_MAINTENANCE_SERVICES, item, "Servicing" in services)
        apply_yes_no(Extras.VEHICLE_SUSPENSION_SERVICES, item, "Suspension & Shock Absorbers" in services)
        apply_yes_no(Extras.VEHICLE_WHEEL_ALIGNMENT_SERVICES, item, "Wheel Alignment" in services)

        yield item
