from scrapy import Spider

from locations.spiders.ladbrokes_gb import LadbrokesGBSpider


class CoralGBSpider(Spider):
    name = "coral_gb"
    item_attributes = {"brand": "Coral", "brand_wikidata": "Q54621344"}
    start_urls = ["https://viewer.blipstar.com/searchdbnew?uid=4566046&lat=53.79&lng=-1.54&type=nearest&value=2000"]

    def parse(self, response):
        yield from LadbrokesGBSpider.parse_response(response)
