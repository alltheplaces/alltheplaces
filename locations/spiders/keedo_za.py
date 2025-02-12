from scrapy import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class KeedoZASpider(Spider):
    name = "keedo_za"
    start_urls = ["https://keedo.co.za/pages/find-a-store"]
    item_attributes = {
        "brand": "Keedo",
        "brand_wikidata": "Q130351264",
    }
    no_refs = True

    def parse(self, response):
        for province in response.xpath('.//div[@class="card__content"]'):
            province_name = province.xpath(".//h3/text()").get()
            for location in province.xpath(".//p"):
                item = Feature()
                item["state"] = province_name
                item["branch"] = location.xpath(".//strong/text()").get().strip()
                info = location.xpath("text()").getall()
                phone = [i for i in info if "Tel:" in i][0]
                item["phone"] = phone.replace("Tel:", "")
                info.remove(phone)
                item["addr_full"] = clean_address(info)
                try:
                    int(info[-1])
                    item["postcode"] = info[-1]
                except ValueError:
                    pass
                yield item
