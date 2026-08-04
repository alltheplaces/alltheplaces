import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class MoleCountryStoresGBSpider(JSONBlobSpider):
    name = "mole_country_stores_gb"
    item_attributes = {"brand": "Mole Valley Farmers", "brand_wikidata": "Q6895915"}
    start_urls = ["https://www.moleonline.com/storelocator/"]

    def extract_json(self, response):
        data_raw = response.xpath('//script[@type="text/x-magento-init"][contains(text(), "marker")]/text()').get()
        return chompjs.parse_js_object(data_raw)["*"]["mvstorelocator"]["stores"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["name"] = "Mole Country Stores"
        apply_category(Categories.SHOP_COUNTRY_STORE, item)
        yield item
