import scrapy
from scrapy.http import Response

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EuromasterNLSpider(StructuredDataSpider):
    name = "euromaster_nl"
    start_urls = ["https://www.euromaster.nl/garages"]
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
        shops = set(response.xpath("//a[text()='Meer informatie']/@href").getall())
        for shop in shops:
            yield scrapy.Request(url=shop, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Euromaster ")
        item["website"] = response.url
        oh = OpeningHours()
        days = response.xpath('//*[@class="tableHoraires"]/tr/th/text()').getall()
        hours = response.xpath('//*[@class="tableHoraires"]/tr/td/text()').getall()
        for day, hour in zip(days, hours):
            oh.add_ranges_from_string(ranges_string=day + " " + hour, days=DAYS_NL, delimiters=[" - "])
        item["opening_hours"] = oh
        yield item
