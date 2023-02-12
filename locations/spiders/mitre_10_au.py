import json

import scrapy

from locations.structured_data_spider import StructuredDataSpider


class Mitre10AUSpider(StructuredDataSpider):
    name = "mitre_10_au"
    item_attributes = {"brand": "Mitre 10", "brand_wikidata": "Q6882393"}
    allowed_domains = ["mitre10.com.au"]
    start_urls = ["https://www.mitre10.com.au/stores"]

    def parse(self, response):
        data_raw = response.xpath(
            '//div[contains(@class, "store-search")]/following::script[@type="text/x-magento-init"]/text()'
        ).extract_first()
        data_clean = " ".join(data_raw.splitlines()).replace("\\/", "/")
        data_json = json.loads(data_clean)
        stores = data_json["*"]["Magento_Ui/js/core/app"]["components"]["store-locator-search"]["markers"]
        # Note that the stores data obtained at this point is missing
        # opening hours which is only available on separate request
        # to the mitre10.com.au store page for each store.
        for store in stores:
            yield scrapy.Request(store["url"], self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Note that the mitre10.com.au store page for each store has
        # linked data that has already been parsed by this point.
        # However, the linked data is missing some fields of
        # information that is found in a separate JavaScript blob on
        # the same page. The following code seeks to complete the
        # missing data.
        data_raw = response.xpath(
            '//div[contains(@class, "store-locator-content")]/following::script[@type="text/x-magento-init"]/text()'
        ).extract_first()
        data_clean = " ".join(data_raw.splitlines()).replace("\\/", "/")
        data_json = json.loads(data_clean)
        stores = data_json["*"]["Magento_Ui/js/core/app"]["components"]["preferred-store"]["children"][
            "retailer-switcher"
        ]["storeOffers"]
        for store in stores:
            if store["address_data"]["latitude"] == item["lat"] and store["address_data"]["longitude"] == item["lon"]:
                item["ref"] = store["sellerId"]
                item["postcode"] = store["address_data"]["postcode"]
                break
        if "mitre10official" in item["facebook"]:
            item.pop("facebook")
        yield item
