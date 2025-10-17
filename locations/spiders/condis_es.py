import re

from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours, sanitise_day


class CondisESSpider(Spider):
    name = "condis_es"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = {"brand": "Condis", "brand_wikidata": "Q57417581"}
    start_urls = ["https://www.condis.es/data/get-tiendas.php"]

    def parse(self, response):
        for location in response.json():
            yield JsonRequest(
                url="https://www.condis.es/ficha/" + str(location["id"]),
                cb_kwargs=dict(location=location),
                callback=self.store_data,
            )

    def store_data(self, response, location):
        item = DictParser.parse(location)
        item["street_address"] = location["calle"]
        item["city"] = location["ciudad"]
        item["postcode"] = location["cp"]
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for timing in response.xpath('//table//table//td[@class="force-col"]'):
            opening_hours = timing.xpath(".//table//tr//td/text()").getall()
            if len(opening_hours) > 1:
                if day := sanitise_day(opening_hours[0].strip(), DAYS_ES):
                    for hours in opening_hours[1:]:
                        # e.g. 09:00-14:00-21:00 replaced by 09:00-21:00
                        hours = re.sub(r"(\d+:\d+)[-\s]+\d+:\d+[-\s]+(\d+:\d+)", r"\1-\2", hours.strip())

                        if match := re.search(r"(\d+:\d+)[-\s]+(\d+:\d+)", hours):
                            item["opening_hours"].add_range(day, match.group(1), match.group(2))
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
