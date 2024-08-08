import scrapy

from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CooplandsDoncasterGBSpider(scrapy.Spider):
    name = "cooplands_doncaster_gb"
    allowed_domains = ["cooplands.co.uk"]
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q96622197", "extras": Categories.SHOP_BAKERY.value}
    start_urls = ["https://cooplands.co.uk/shop-locations"]

    def __init__(self):
        self.item_attributes["opening_hours"] = OpeningHours()
        for day in DAYS[0:6]:
            self.item_attributes["opening_hours"].add_range(day=day, open_time="08:00", close_time="17:00")

    def parse(self, response):
        stores = response.xpath("//div[@class='box box-store']")

        for index, store in enumerate(stores):
            data = store.xpath("ul/li/text()").extract()
            addr_full = merge_address_lines(data[:-1])

            yield Feature(
                ref=index,
                name=store.xpath("h4/text()").extract_first(),
                addr_full=addr_full,
                postcode=data[-2].strip(),
                phone=data[-1].strip(),
            )
