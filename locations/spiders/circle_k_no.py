from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import sanitise_day
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class CircleKNOSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_no"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.no/stations"]
    rules = [Rule(LinkExtractor(allow=r"/station/circle-k-[-\w]+/?$"), callback="parse")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        if any(sanitise_day(rule) for rule in ld_data.get("openingHours", [])):  # day without hours
            ld_data.pop("openingHours")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = self.item_attributes["brand"]
        if not ld_data.get("openingHours"):
            ld_data["openingHours"] = []
            for rule in response.xpath('//*[@itemprop="openingHours"]'):
                day = rule.xpath("./@content").get()
                hours = rule.xpath("./text()").get("").replace("Døgnåpent", "00:00-23:59")  # open 24 hours
                ld_data["openingHours"].append(f"{day} {hours}")
        try:
            item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld_data)
        except:
            self.logger.error(f'Failed to parse opening hours: {ld_data.get("openingHours")}')
            item["opening_hours"] = None

        extract_google_position(item, response)

        fuels = [
            fuel.split("FeatureFuel")[-1]
            for fuel in response.xpath('//img[contains(@src,"FeatureFuel")]/@src').getall()
        ]
        charging_station = response.xpath('//img[contains(@src,"FeatureEVCharger")]/@src').get()
        if not fuels and charging_station:
            apply_category(Categories.CHARGING_STATION, item)
        else:
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.ELECTRIC, item, bool(charging_station))

        apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in fuels)
        apply_yes_no(Fuel.OCTANE_95, item, "Miles95" in fuels)
        apply_yes_no(Fuel.OCTANE_95, item, "MilesPlus95" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesDiesel" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesPlusDiesel" in fuels)
        apply_yes_no(Fuel.UNTAXED_DIESEL, item, "Anleggsdiesel" in fuels)
        apply_yes_no(Fuel.BIODIESEL, item, "MilesBioHVO100" in fuels)
        yield item
