import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class CooplandsDoncasterSpider(scrapy.Spider):
    name = "cooplands_doncaster"
    allowed_domains = ["cooplands.co.uk"]
    item_attributes = {
        "brand": "Cooplands",
        "brand_wikidata": "Q96622197",
        "country": "GB",
    }
    start_urls = ["https://cooplands.co.uk/shop-locations"]

    def __init__(self):
        self.item_attributes["opening_hours"] = OpeningHours()
        for day in DAYS[0:6]:
            self.item_attributes["opening_hours"].add_range(day=day, open_time="08:00", close_time="17:00")

    def parse(self, response):
        stores = response.xpath("//div[@class='box box-store']")

        for index, store in enumerate(stores):
            data = store.xpath("ul/li/text()").extract()
            addr_full = clean_address(data[:-1])

            yield Feature(
                ref=index,
                name=store.xpath("h4/text()").extract_first(),
                addr_full=addr_full,
                postcode=data[-2].strip(),
                phone=data[-1].strip(),
            )
