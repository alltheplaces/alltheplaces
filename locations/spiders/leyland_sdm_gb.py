from typing import Iterable

from scrapy import Selector

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LeylandSdmGBSpider(AmastyStoreLocatorSpider):
    name = "leyland_sdm_gb"
    item_attributes = {"brand": "Leyland SDM", "brand_wikidata": "Q110437963"}
    allowed_domains = ["leylandsdm.co.uk"]

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["name"] = item["name"].strip()
        item["street_address"] = popup_html.xpath("//text()[4]").get().replace("Address:", "")
        item["city"] = popup_html.xpath("//text()[5]").get().replace("City:", "")
        item["postcode"] = popup_html.xpath("//text()[6]").get().replace("Postcode:", "")
        item["phone"] = popup_html.xpath("//text()[7]").get()
        item["website"] = popup_html.xpath("//@href").get().replace("Maida Vale/", "Maida%20Vale/")
        yield item
