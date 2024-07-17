from scrapy import Spider

from locations.categories import Categories
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class KrispyKremeMXSpider(Spider):
    name = "krispy_kreme_mx"
    item_attributes = {"brand": "Krispy Kreme", "brand_wikidata": "Q1192805", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://www.krispykreme.mx/directorio-tiendas/"]
    no_refs = True

    def parse(self, response):
        locations = response.xpath('//tbody[@id="myTable"]/tr')
        for index in range(0, len(locations)):
            item = {}
            # item["name"] = locations[index].xpath('./td[1]/text()').get() # Seems to be name of owner or something. Thus use NSI Name tag
            item["addr_full"] = clean_address(locations[index].xpath("./td[2]/text()").get())
            if phone := locations[index].xpath("./a/text()").get():
                item["phone"] = phone

            yield Feature(**item)
