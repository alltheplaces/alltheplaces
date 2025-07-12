from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class BytefederalAUSpider(Spider):
    name = "bytefederal_au"
    item_attributes = {"brand": "ByteFederal", "brand_wikidata": "Q135284926"}
    allowed_domains = ["www.bytefederal.au"]
    start_urls = ["https://www.bytefederal.au/bitcoin-atm-near-me?latitude=0&longitude=0"]

    def parse(self, response: Response) -> Iterable[Feature]:
        locations_js = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = parse_js_object(locations_js)["props"]["pageProps"]["locations"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = str(item["ref"])
            item["website"] = "https://www.bytefederal.au/bitcoin-atm-near-me/{}/{}/{}?country=australia".format(
                location["state"].lower(), location["city"].lower().replace(" ", "-"), location["id"]
            )
            item["image"] = location["photo_url"]

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, location["open_hour"], location["close_hour"], "%H:%M:%S")

            apply_category(Categories.ATM, item)
            item["extras"]["currency:XBT"] = "yes"
            item["extras"]["currency:SATS"] = "yes"
            item["extras"]["currency:ETH"] = "yes"
            item["extras"]["currency:DOGE"] = "yes"
            item["extras"]["currency:LTC"] = "yes"
            item["extras"]["currency:AUD"] = "yes"
            item["extras"]["cash_in"] = "yes"
            apply_yes_no("cash_out", item, location["location_type"] != "one way", False)

            yield item
