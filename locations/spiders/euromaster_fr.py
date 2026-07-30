import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EuromasterFRSpider(StructuredDataSpider):
    name = "euromaster_fr"
    start_urls = ["https://www.euromaster.fr/centres"]
    item_attributes = {"brand": "Euromaster", "brand_wikidata": "Q3060668"}

    def parse(self, response):
        regions = response.xpath('//*[@class="list-province w-100"]//@href').getall()
        for region in regions:
            yield scrapy.Request(url=region, callback=self.parse_region)

    def parse_region(self, response):
        cities = response.xpath('//*[@class="list-province w-100"]//@href').getall()
        for city in cities:
            yield scrapy.Request(url=city, callback=self.parse_city)

    def parse_city(self, response):
        shops = set(response.xpath("//a[text()='Voir la fiche centre']/@href").getall())
        for shop in shops:
            yield scrapy.Request(url=shop, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # NSI has exactly one Euromaster entry (only covering "fx", the
        # legacy code for Metropolitan France that the location matcher does
        # not alias to "fr"), so apply the category directly rather than
        # relying on NSI location matching.
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        item["website"] = response.url
        oh = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            day = sanitise_day(day_time["dayOfWeek"], DAYS_FR)
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
        item["opening_hours"] = oh
        yield item
