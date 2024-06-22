import json
from html import unescape

from scrapy import Request, Selector
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_FR, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class MicromaniaFRSpider(StructuredDataSpider):
    name = "micromania_fr"
    item_attributes = {"brand": "Micromania", "brand_wikidata": "Q3312221", "extras": Categories.SHOP_VIDEO_GAMES.value}
    allowed_domains = ["www.micromania.fr"]
    start_urls = [
        "https://www.micromania.fr/on/demandware.store/Sites-Micromania-Site/default/Stores-FindStoresLocator?radius=3000&postalCode=*"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        locations = json.loads(response.json()["locations"])
        for location in locations:
            html_blob = Selector(text=location["infoWindowHtml"])
            store_page = html_blob.xpath('//a[contains(@class, "info-window__magazine-link")]/@href').get()
            yield Request(url=store_page, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        item["ref"] = response.url.split("?storeid=", 1)[1]
        item["street_address"] = clean_address(
            response.xpath(
                '//p[@itemprop="address"]//text()/parent::*[@itemprop="streetAddress" or @itemprop="address"]/text()'
            ).getall()
        )
        item.pop("facebook", None)
        item.pop("twitter", None)

        hours_json_string = unescape(" ".join(response.xpath('//span[@itemprop="openingHours"]/text()').getall()))
        hours_json = json.loads(hours_json_string)
        item["opening_hours"] = OpeningHours()
        for day_hours in hours_json.values():
            if day_hours["ouverture"] == day_hours["fermeture"]:
                continue
            item["opening_hours"].add_range(
                DAYS_FR[day_hours["name"]], day_hours["ouverture"], day_hours["fermeture"], "%H:%M:%S"
            )

        yield item
