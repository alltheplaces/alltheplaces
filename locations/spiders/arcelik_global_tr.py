from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS

BRANDS = {
    "arcelik": {"brand": "Arçelik", "brand_wikidata": "Q640497"},
    "beko": {"brand": "Beko", "brand_wikidata": "Q631792"},
}


class ArcelikGlobalTRSpider(Spider):
    name = "arcelik_global_tr"
    start_urls = ["https://www.arcelik.com.tr/arcelik-magazalari", "https://www.beko.com.tr/beko-magazalari"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response, **kwargs):
        for location in response.xpath('//*[@class="srv-item "][@data-order]'):
            item = Feature()
            item["website"] = response.url
            item["lat"], item["lon"] = location.xpath("./@data-coor").get().split("|")
            item["name"] = location.xpath('.//*[@class="srv-name"]/text()').get().replace("\n", " ").strip()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="srv-address"]/text()').get())
            item["phone"] = location.xpath('.//*[contains(@data-href, "tel:")]/@data-href').get()
            for key, value in BRANDS.items():
                if key in response.url:
                    item.update(BRANDS[key])
                    item["ref"] = " - ".join([location.xpath("./@data-order").get(), key])

            apply_category(Categories.SHOP_APPLIANCE, item)

            yield item
