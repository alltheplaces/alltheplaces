import re

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class PlodineHRSpider(Spider):
    name = "plodine_hr"
    item_attributes = {"brand": "Plodine", "brand_wikidata": "Q58040098"}
    start_urls = ["https://www.plodine.hr/supermarketi"]
    zipcode_pattern = r"^\W*(\d{5})\W*(\w.+\w)\W*$"

    def parse(self, response: Response):
        for details, marker in zip(response.xpath('//li[@class="market "]'), response.xpath('//div[@class="marker"]')):
            street_address, city_line, *_ = details.xpath('.//div[@class="market__location"]/p/text()').getall()
            postcode, city = re.findall(self.zipcode_pattern, city_line)[0]
            opening_hours = OpeningHours()
            day_ranges = [DAYS_WEEKDAY, ["Saturday"], ["Sunday"]]
            hour_ranges = details.xpath('.//div[@class="market__workhours"]/div/strong')
            for day_range, hour_range in zip(day_ranges, hour_ranges):
                if hour_range.xpath("./@class").get() == "closed":
                    continue
                open, close = hour_range.xpath("./text()").get().split("-")
                opening_hours.add_days_range(day_range, open, close)

            yield Feature(
                ref=details.xpath(".//a/@href").get().split("/")[-2],
                lat=marker.attrib["data-lat"],
                lon=marker.attrib["data-lng"],
                street_address=street_address,
                postcode=postcode,
                city=city,
                opening_hours=opening_hours,
            )
