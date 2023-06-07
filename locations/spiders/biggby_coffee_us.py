from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BiggbyCoffeeUSSpider(Spider):
    name = "biggby_coffee_us"
    item_attributes = {"brand": "Biggby Coffee", "brand_wikidata": "Q4906876"}
    allowed_domains = ["www.biggby.com"]
    start_urls = ["https://www.biggby.com/locations/"]

    def parse(self, response):
        for location in response.xpath("(//markers)[1]/marker"):
            if location.attrib["coming-soon"]:
                continue
            item = DictParser.parse(location.attrib)
            item["street_address"] = ", ".join(
                filter(None, [location.attrib["address-one"], location.attrib["address-two"]])
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(
                ["Mo", "Tu", "We", "Th"], location.attrib["mon-thurs-open-hour"], location.attrib["mon-thurs-open-hour"]
            )
            item["opening_hours"].add_range("Fr", location.attrib["fri-open-hour"], location.attrib["fri-close-hour"])
            item["opening_hours"].add_range("Sa", location.attrib["sat-open-hour"], location.attrib["sat-close-hour"])
            item["opening_hours"].add_range("Su", location.attrib["sun-open-hour"], location.attrib["sun-close-hour"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.attrib["drive-thru"], False)
            apply_yes_no(Extras.WIFI, item, location.attrib["wifi"], False)
            yield item
