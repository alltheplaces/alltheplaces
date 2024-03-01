from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class CentraIESpider(Spider):
    name = "centra_ie"
    item_attributes = {"brand": "Centra", "brand_wikidata": "Q747678"}
    start_urls = ["https://centra.ie/request/component/ecommerce/store_list"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="listing"]/div'):
            item = Feature()
            item["ref"] = location.xpath('./div[@class="shop-info"]/a/@href').re_first(r"_(\d+)$")
            item["name"] = location.xpath('.//h4[@class="shop-title"]/text()').get()
            item["addr_full"] = location.xpath('.//p[@class="shop-address"]/text()').get()
            item["phone"] = location.xpath('.//li[@class="call"]/a/@href').get().replace("tel:", "")
            item["lat"], item["lon"] = (
                location.xpath('.//li[@class="directions"]/a/@onclick')
                .re_first(r"\((-?\d+\.\d+,\s-?\d+\.\d+)\);")
                .split(", ")
            )

            apply_category(Categories.SHOP_CONVENIENCE, item)

            services = location.xpath('.//div[@class="store-taxonomy"]/ul/li/text()').getall()

            apply_yes_no(Extras.ATM, item, "ATM" in services)
            apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Accessible" in services)
            apply_yes_no("sells:alcohol", item, "Off Licence" in services)
            apply_yes_no("sells:lottery", item, "Lotto" in services)

            yield item
