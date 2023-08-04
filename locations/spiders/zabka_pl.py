import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ZabkaPLSpider(scrapy.Spider):
    name = "zabka_pl"
    item_attributes = {"brand": "Żabka", "brand_wikidata": "Q2589061"}

    # URL extracted by observing request made by Żappka Android app (using HTTP Toolkit)
    start_urls = ["https://partner-api.zabkamobile.pl/v2/shops"]

    def start_requests(self):
        # Authorization header is hard-coded into the Żappka app and does not appear to change (as of version 3.14.10).
        headers = {
            "Authorization": "PartnerKey 424A0B7AD0E9EA136510474D89061BBDC007B9BE5256A638EA28CC19D2BB15CD",
        }
        yield JsonRequest(url=self.start_urls[0], headers=headers)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", "")
            # unset "state" field, it is taken from the "region" field which is some internal Żabka ID
            item["state"] = None
            item["opening_hours"] = OpeningHours()

            # Each franchisee is required to be open Mon-Sat with the same hours
            # But the hours for Sundays are set in the "nonTradingDays" field, which
            # contains the opening hours for each specific Sunday.
            item["opening_hours"].add_days_range(
                ["Mo", "Tu", "We", "Th", "Fr", "Sa"], location["openTime"], location["closeTime"]
            )
            yield item
