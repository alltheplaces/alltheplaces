from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class LombardAUSpider(Spider):
    name = "lombard_au"
    item_attributes = {"brand": "Lombard", "brand_wikidata": "Q140682045"}
    allowed_domains = ["www.lombard.com.au"]
    start_urls = ["https://www.lombard.com.au/site/pages/party-shop-finder"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {}
        for store in response.xpath("//table/tbody/tr"):
            if store.xpath('./td[@colspan="6"]'):
                lat, lon = url_to_coords(
                    store.xpath('.//iframe[contains(@src, "https://www.google.com/maps/embed")]/@src').get()
                )
                if lat and lon and "branch" in properties.keys():
                    properties["lat"] = lat
                    properties["lon"] = lon
                    apply_category(Categories.SHOP_PARTY, properties)
                    yield Feature(**properties)
            else:
                properties = {
                    "branch": store.xpath("./td[1]//text()").get().strip(),
                    "addr_full": merge_address_lines(
                        store.xpath('./td[contains(@class, "party-shop-finder-address")]//text()').getall()
                    ),
                    "opening_hours": OpeningHours(),
                    "phone": store.xpath('./td/a[contains(@href, "tel:")]/@href').get().removeprefix("tel:"),
                }
                if "Events By Lombard" in properties["branch"]:
                    properties = {}
                    continue
                hours_string = " ".join(
                    filter(
                        None,
                        map(
                            str.strip,
                            store.xpath('./td[contains(@class, "party-shop-finder-trading-hours")]//text()').getall(),
                        ),
                    )
                )
                properties["opening_hours"].add_ranges_from_string(hours_string)
