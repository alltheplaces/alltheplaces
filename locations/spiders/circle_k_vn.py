from scrapy import Spider

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CircleKVNSpider(Spider):
    name = "circle_k_vn"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.com.vn/en/store-locator/"]

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@class="item"]'):
            item = Feature()
            item["ref"] = store.xpath(".//@data-index").get()
            item["addr_full"] = merge_address_lines(store.xpath("./p/text()").getall())
            item["lat"] = store.xpath(".//@data-lat").get()
            item["lon"] = store.xpath(".//@data-lng").get()
            item["name"] = "Circle K"
            item["website"] = response.url
            services = [service.lower() for service in store.xpath(".//@title").getall()]
            apply_yes_no(Extras.ATM, item, "atm" in services)
            apply_yes_no("payment:terminal", item, "bill payment" in services)
            apply_yes_no(PaymentMethods.CARDS, item, "card payment" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "store with seats" in services)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
