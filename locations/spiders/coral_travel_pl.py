from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class CoralTravelPLSpider(CrawlSpider):
    name = "coral_travel_pl"
    item_attributes = {"brand": "Coral Travel", "brand_wikidata": "Q58011479"}
    start_urls = ["https://www.coraltravel.pl/travel-offices"]
    rules = [Rule(LinkExtractor(r"/travel-offices/.+/.+$"), callback="parse")]
    wanted_types = ["TravelAgency"]

    def parse(self, response, **kwargs):
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url.split("/")[-1]

        if destination_text := response.xpath('//a[contains(@href, "destination=")]/@href').get():
            item["lat"], item["lon"] = destination_text.split("destination=")[-1].split(",")

        address_lines = list(
            filter(
                lambda line: len(line) > 0,
                map(str.strip, response.xpath('//p[a[contains(@href, "destination=")]]/text()').get().split("\n")),
            )
        )
        post_code_city = address_lines[-1]
        item["street_address"] = address_lines[-2]
        item["postcode"] = post_code_city.split(" ")[0]
        item["city"] = " ".join(post_code_city.split(" ")[1:])

        item["opening_hours"] = OpeningHours()
        open_hour_lines = response.xpath('//div[h3[text()="Godziny otwarcia"]]/ul/li/text()').getall()
        for index in range(0, len(open_hour_lines), 2):
            days = open_hour_lines[index]
            hours = open_hour_lines[index + 1]
            item["opening_hours"].add_ranges_from_string(ranges_string=f"{days} {hours}", days=DAYS_PL)

        yield item
