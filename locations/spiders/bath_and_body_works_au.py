from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.bath_and_body_works_us import BathAndBodyWorksUSSpider


class BathAndBodyWorksAUSpider(JSONBlobSpider):
    name = "bath_and_body_works_au"
    item_attributes = BathAndBodyWorksUSSpider.item_attributes
    allowed_domains = ["www.bathandbodyworks.com.au"]
    start_urls = [
        "https://www.bathandbodyworks.com.au/on/demandware.store/Sites-bbw-aus-Site/en_AU/Stores-FindStores?showMap=true&postalCode=Melbourne&radius=30000&storeType=bbw&storeType=bbw_outlet&storeType=white_barn&latitude=-37.8136276&longitude=144.9630576&countryCode=AU"
    ]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("BATH & BODY WORKS ").removeprefix("Bath & Body Works ")
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        item["website"] = "https://www.bathandbodyworks.com.au/" + feature["ID"] + ".html"
        hours_html = Selector(text=feature["storeHours"])
        hours_text = " ".join(hours_html.xpath('//span[@class="sl-weekday" or @class="sl-time"]/text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
