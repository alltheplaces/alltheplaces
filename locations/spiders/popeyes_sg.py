import scrapy

from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class PopeyesSGSpider(scrapy.Spider):
    name = "popeyes_sg"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    start_urls = ["https://www.popeyes.com.sg/FindPopeyes.html"]

    def parse(self, response, **kwargs):
        for store in response.xpath(r'//*[@class = "location-box"]'):
            item = Feature()
            item["name"] = item["ref"] = store.xpath("./h4//text()").get()
            item["street"] = store.xpath("./p/text()").get()
            item["housenumber"] = store.xpath("./p/text()[2]").get().replace(" ", "").replace("\n", "")
            item["addr_full"] = clean_address(
                ",".join([item["street"], item["housenumber"], store.xpath("./p/text()[3]").get()])
            )
            item["website"] = "https://www.popeyes.com.sg/"
            yield item
