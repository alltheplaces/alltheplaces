from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class OdidoPLSpider(Spider):
    name = "odido_pl"
    item_attributes = {"brand": "Odido", "brand_wikidata": "Q106947294"}
    start_urls = [
        "https://www.sklepy-odido.pl//sxa/search/results/?s={F2EE6EC1-265E-466C-88DA-EFF88C6451FC}&itemid={66EC78FE-140F-474C-AE5A-F3BE13297A32}&sig=store-locator&g=%7C&o=StoreName%2CAscending&p=10000&v=%7B0481E249-4813-49C4-8836-5E1A48614186%7D"
    ]

    def parse(self, response, **kwargs):
        for feature in response.json()["Results"]:
            item = DictParser.parse(feature)
            website_suffix = feature["Url"].split("/")[-1]
            item["website"] = f"https://www.sklepy-odido.pl/znajdz-sklep/{website_suffix}"
            yield Request(
                url=item["website"],
                callback=self.parse_store,
                cb_kwargs={"item": item},
            )

    def parse_store(self, response, item):
        item["opening_hours"] = OpeningHours()
        item["addr_full"] = response.xpath('//a[@class="store-address"]/text()').get()
        days = response.xpath('//span[contains(@class, "days")]/text()').getall()
        hour_ranges = response.xpath('//span[contains(@class, "field-hours-for-customer")]/text()').getall()
        for day, hour_range in zip(days, hour_ranges):
            item["opening_hours"].add_ranges_from_string(f"{day} {hour_range}", days=DAYS_PL)
        yield item
