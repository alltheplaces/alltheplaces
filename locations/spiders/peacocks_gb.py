from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PeacocksGBSpider(Spider):
    name = "peacocks_gb"
    item_attributes = {"brand": "Peacocks", "brand_wikidata": "Q7157762"}
    start_urls = [
        "https://www.peacocks.co.uk/on/demandware.store/Sites-peacocks-Site/default/Stores-FindStores?radius=1000&lat=51.5072178&long=-0.1275862",
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["website"] = store["storeDetailsURL"]
            item["branch"] = item.pop("name").removeprefix("PEACOCKS ")

            item["opening_hours"] = self.parse_opening_hours(Selector(text=store["storeHours"]))

            yield item

    def parse_opening_hours(self, sel: Selector) -> OpeningHours:
        oh = OpeningHours()
        columns = iter(sel.xpath('//*[@class="store-hours"]//td/text()'))
        for r in columns:
            day = r.get().rstrip(":")
            time = next(columns).get()
            if time == "CLOSED":
                oh.set_closed(day)
            else:
                start_time, end_time = time.replace(":", ".").split("-")
                oh.add_range(day, start_time.strip(), end_time.strip(), time_format="%I.%M%p")
        return oh
