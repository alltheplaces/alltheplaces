import re
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class RoofRacksGaloreAUSpider(Spider):
    name = "roof_racks_galore_au"
    item_attributes = {
        "brand": "Roof Racks Galore",
        "brand_wikidata": "Q126179662",
        "extras": Categories.SHOP_CAR_PARTS.value,
    }
    allowed_domains = ["www.roofracksgalore.com.au"]
    start_urls = ["https://www.roofracksgalore.com.au/locations"]

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        js_blob = response.xpath('//script[contains(text(), "var storelocations = [")]/text()').get()
        js_blob = js_blob.split("var storelocations = [", 1)[1].split("];", 1)[0].strip()
        if m := re.findall(r"\['([\w ]+)', (-?\d+\.\d+), (-?\d+\.\d+),", js_blob):
            for feature in m:
                store_name = feature[0]
                lat = feature[1]
                lon = feature[2]
                url = f"https://www.roofracksgalore.com.au/marcwatts/magento/magento2/storelocater/action/get/collection/database/store/list/magento2-storelocater-get-collection-database-store-list.php?store_name={store_name}&is_postcode_use=1&postcode=&current_long={lon}&current_lat={lat}"
                yield JsonRequest(url=url, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        feature = Selector(text=response.json()["stores"]).xpath("(//li)[1]")

        properties = {
            "ref": feature.xpath("//@data-store-id").get(),
            "branch": feature.xpath('//label[contains(@class, "store-item-lable")]/text()').get().strip(),
            "addr_full": feature.xpath('//span[contains(@class, "address-location")]/text()').get().strip(),
            "phone": feature.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", ""),
            "email": feature.xpath('//a[contains(@href, "mailto:")]/@href').get("").replace("mailto:", ""),
            "opening_hours": OpeningHours(),
        }

        hours_string = " ".join(
            filter(
                None, map(str.strip, feature.xpath('//div[contains(@class, "store-opening-hours")]//text()').getall())
            )
        )
        properties["opening_hours"].add_ranges_from_string(hours_string)

        yield Feature(**properties)
