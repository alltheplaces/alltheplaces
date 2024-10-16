from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_BG, sanitise_day
from locations.spiders.vapestore_gb import clean_address


class MussalaBGSpider(Spider):
    name = "mussala_bg"
    item_attributes = {"brand_wikidata": "Q120314195"}
    start_urls = [
        "https://mussalains.com/wp-admin/admin-ajax.php?action=store_search&lat=43.21405&lng=27.914733&autoload=1"
    ]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location.pop("address"), location.pop("address2")])
            item["opening_hours"] = OpeningHours()
            rows = Selector(text=location["hours"]).xpath("//table/tr").getall()
            for row in rows:
                selector_row = Selector(text=row)
                hours = selector_row.xpath('//td[2]//text()').get()
                if hours == 'Затворено':
                    continue
                day = selector_row.xpath('//td[1]/text()').get()
                day = sanitise_day(day, DAYS_BG)
                start_time, end_time = hours.replace('.', ':').split(" - ")
                item["opening_hours"].add_range(day, start_time, end_time)
            yield item
