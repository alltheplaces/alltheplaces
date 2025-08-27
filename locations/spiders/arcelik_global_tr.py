import scrapy
from scrapy import FormRequest, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

BRANDS = {
    "arcelik": {"brand": "Arçelik", "brand_wikidata": "Q640497"},
    "beko": {"brand": "Beko", "brand_wikidata": "Q631792"},
}


class ArcelikGlobalTRSpider(Spider):
    name = "arcelik_global_tr"
    no_refs = True
    requires_proxy = True

    def start_requests(self):
        for brand in BRANDS.keys():
            url = f"https://www.{brand}.com.tr/{brand}-bayileri"
            yield scrapy.Request(url, cb_kwargs={"brand": brand})

    def parse(self, response, **kwargs):
        brand = kwargs["brand"]
        city_codes = response.xpath('//select[@id="cityCode"]/option')
        for city_code in city_codes[1:]:
            yield FormRequest(
                url=f"https://www.{brand}.com.tr/getStoreFinderUrl",
                method="get",
                formdata={
                    "postCode": city_code.xpath("./@value").get(),
                    "isService": "false",
                },
                callback=self.parse_city_url,
                cb_kwargs={"city": city_code.xpath("./text()").get(), "brand": brand},
            )

    def parse_city_url(self, response, **kwargs):
        yield response.follow(response.text, callback=self.parse_locations, cb_kwargs=kwargs)

    def parse_locations(self, response, **kwargs):
        for location in response.xpath('//*[@class="srv-item "][@data-order]'):
            item = Feature()
            item["website"] = response.url
            item["lat"], item["lon"] = location.xpath("./@data-coor").get().split("|")
            item["name"] = location.xpath('.//*[@class="srv-name"]/text()').get().replace("\n", " ").strip()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="srv-address"]/text()').get())
            item["city"] = kwargs["city"]
            item["phone"] = location.xpath('.//*[contains(@data-href, "tel:")]/@data-href').get()
            item.update(BRANDS[kwargs["brand"]])
            apply_category(Categories.SHOP_APPLIANCE, item)

            yield item
