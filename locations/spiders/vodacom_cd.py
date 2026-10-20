import json
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class VodacomCDSpider(Spider):
    name = "vodacom_cd"
    item_attributes = {"brand": "Vodacom Congo", "brand_wikidata": "Q130477507"}
    start_urls = ["https://www.vodacom.cd/fr/particulier/assisstance/nos-vodashops/find-vodashops"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        settings = json.loads(response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get())
        for marker in settings["leaflet"]["leaflet-map-view-vodashops-page-shop-listing"]["features"]:
            if "lat" not in marker:
                continue
            yield Request(
                url="https://www.vodacom.cd/node/{}".format(marker["entity_id"]),
                callback=self.parse_store,
                cb_kwargs={"lat": marker["lat"], "lon": marker["lon"]},
            )

    def parse_store(self, response: Response, lat: float, lon: float) -> Iterable[Feature]:
        if response.xpath('//div[contains(@class, "field--name-field-shoptype")]/text()').get() != "VodaShop":
            return

        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[-1]
        item["branch"] = response.xpath("//title/text()").get().split("|")[0].strip()
        item["street_address"] = response.xpath('//div[contains(@class, "field--name-field-address")]/p/text()').get()
        item["city"] = response.xpath('//div[contains(@class, "field--name-field-city")]/text()').get()
        item["state"] = response.xpath('//div[contains(@class, "field--name-field-region")]//text()').get()
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
