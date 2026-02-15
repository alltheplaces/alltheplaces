import chompjs
import scrapy
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class EnergieFitnessGBIESpider(scrapy.Spider):
    name = "energie_fitness_gb_ie"
    item_attributes = {"brand": "énergie Fitness", "brand_wikidata": "Q109855553"}
    start_urls = ["https://energiefitness.com/find-a-gym"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response):
        gyms = chompjs.parse_js_object(response.xpath('//script[contains(text(), "window.mapData")]/text()').get())
        for gym in gyms:
            yield scrapy.Request(
                url=response.urljoin(gym["view_url"]),
                callback=self.parse_gym,
                cb_kwargs={"gym": gym},
            )

    def parse_gym(self, response: Response, gym: dict):
        item = Feature()
        item["ref"] = gym["id"]
        item["branch"] = gym["name"].removesuffix(" Gym")
        item["lat"] = float(gym["latitude"])
        item["lon"] = float(gym["longitude"])
        item["addr_full"] = gym["address_concated"]
        item["country"] = gym["country_code"]
        item["postcode"] = gym["postcode"]
        item["website"] = response.url

        ld_item = LinkedDataParser.find_linked_data(response, "ExerciseGym")
        if ld_item:
            item["email"] = LinkedDataParser.get_case_insensitive(ld_item, "email")
            item["phone"] = LinkedDataParser.get_case_insensitive(ld_item, "telephone")

        oh = OpeningHours()
        for div in response.xpath('//div[@class="opening_time"]'):
            text = " ".join(div.xpath(".//text()").getall())
            oh.add_ranges_from_string(text.replace("24 hours", "00:00-24:00"))
        item["opening_hours"] = oh

        yield item
