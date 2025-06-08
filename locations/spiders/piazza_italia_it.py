import logging
import re

import chompjs

from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class PiazzaItaliaITSpider(JSONBlobSpider):
    name = "piazza_italia_it"
    item_attributes = {"brand": "Piazza Italia", "brand_wikidata": "Q3902241"}
    allowed_domains = ["www.piazzaitalia.it"]
    start_urls = ["https://www.piazzaitalia.it/it-it/store-locator"]
    re_period = re.compile(r"\s*[,;]\s*")

    def extract_json(self, response):
        store_locator_data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "loaderData")][1]/text()').get()
        )
        return store_locator_data["state"]["loaderData"]["routes/($lang).store-locator"]["stores"]

    def pre_process_data(self, location):
        location["website"] = "https://www.piazzaitalia.it/it-it/store-locator/" + location["handle"]
        location["ref"] = location.pop("handle")
        location["street_address"] = location.pop("address")

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        hours = OpeningHours()
        for index, day in enumerate(DAYS):
            day_definition = location["openings"][str(index + 1)]
            for period in self.re_period.split(day_definition):
                if "-" in period:
                    try:
                        open_time, close_time = period.split("-")
                        hours.add_range(day, open_time.strip(), close_time.strip(), "%H:%M")
                    except ValueError:
                        logging.warning("Invalid opening hours period '%s'", period)
        item["opening_hours"] = hours
        yield item
