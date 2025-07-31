import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MrSubCASpider(scrapy.Spider):
    name = "mr_sub_ca"
    item_attributes = {"brand": "Mr. Sub", "brand_wikidata": "Q6929225"}
    start_urls = ["https://mrsub.ca/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response, **kwargs):
        for store in response.xpath("/locator/store/item"):
            item = Feature()
            item["addr_full"] = clean_address(store.xpath("./address/text()").get())
            item["lat"] = store.xpath("./latitude/text()").get()
            item["lon"] = store.xpath("./longitude/text()").get()
            item["ref"] = store.xpath("./storeId/text()").get()
            item["website"] = store.xpath("./exturl/text()").get()
            item["phone"] = store.xpath("./telephone/text()").get()
            item["postcode"] = store.xpath("./country/text()").get()
            apply_category(Categories.FAST_FOOD, item)
            yield item
