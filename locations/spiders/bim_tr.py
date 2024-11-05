import scrapy
from scrapy import FormRequest, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BimTRSpider(Spider):
    name = "bim_tr"
    item_attributes = {"brand": "BİM", "brand_wikidata": "Q1022075"}
    start_urls = ["https://www.bim.com.tr/Categories/104/magazalar.aspx"]
    no_refs = True

    def parse(self, response, **kwargs):
        city_list = response.xpath('//select[@id="BimFiltre_DrpCity"]/option')
        for city in city_list:
            city_name = city.xpath("./text()").get()
            city_key = city.xpath("./@value").get()
            yield FormRequest(
                url=response.url,
                formdata={"BimFiltre$DrpCity": city_key},
                callback=self.parse_county,
                cb_kwargs=dict(city_name=city_name, city_key=city_key),
            )

    def parse_county(self, response, **kwargs):
        county_list = response.xpath('//select[@id="BimFiltre_DrpCounty"]/option')
        for county in county_list:
            county_key = county.xpath("./@value").get()
            yield FormRequest(
                url=response.url,
                method="GET",
                formdata={"CityKey": kwargs["city_key"], "CountyKey": county_key},
                callback=self.parse_stores,
                cb_kwargs=kwargs,
            )

    def parse_stores(self, response, **kwargs):
        for store in response.xpath('//*[@class="detailArea"]//*[@class="title"]'):
            item = Feature()
            item["branch"] = store.xpath("./text()").get()
            item["addr_full"] = clean_address(store.xpath("./following::p/text()").get())
            item["city"] = kwargs["city_name"]
            item["website"] = response.url
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
