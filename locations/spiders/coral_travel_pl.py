from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_PL, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CoralTravelPLSpider(CrawlSpider, StructuredDataSpider):
    name = "coral_travel_pl"
    item_attributes = {"brand": "Coral Travel", "brand_wikidata": "Q58011479"}
    start_urls = ["https://www.coraltravel.pl/biura-podrozy"]
    rules = [Rule(LinkExtractor("/biura-podrozy/.+/.+/.+$"), callback="parse_sd")]
    wanted_types = ["TravelAgency"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//input[@id="map_position_lat"]/@value').get()
        item["lon"] = response.xpath('//input[@id="map_position_lng"]/@value').get()

        address_lines = list(
            filter(
                lambda line: len(line) > 0,
                map(str.strip, response.xpath("//div[@class='saleAdress']/text()").getall()),
            )
        )
        post_code_city = address_lines[-1]
        item["street_address"] = address_lines[-2]
        item["postcode"] = post_code_city.split(" ")[0]
        item["city"] = " ".join(post_code_city.split(" ")[1:])

        item["opening_hours"] = OpeningHours()
        for open_hour_div in response.xpath("//div[@class='openContainer']"):
            texts = open_hour_div.xpath("span/text()").getall()
            if len(texts) != 3:
                continue
            day, open_time, close_time = texts
            item["opening_hours"].add_ranges_from_string(ranges_string=f"{day} {open_time}-{close_time}", days=DAYS_PL)

        yield item
