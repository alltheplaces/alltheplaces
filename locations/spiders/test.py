from scrapy import Spider

from locations.hours import OpeningHours


class TestSpider(Spider):
    name = "test"

    def start_requests(self):
        oh = OpeningHours()
        oh.add_range("Sa", "16:00", "03:00")
        oh.add_range("Su", "16:00", "23:00")
        print(oh.as_opening_hours())
