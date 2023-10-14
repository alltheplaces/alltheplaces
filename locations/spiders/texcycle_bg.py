from scrapy import Spider

from locations.items import Feature


class TexcycleBGSpider(Spider):
    name = "texcycle_bg"
    item_attributes = {"brand": "TexCycle", "brand_wikidata": "Q85614408"}
    allowed_domains = ["www.texcycle.bg"]
    start_urls = ["https://texcycle.bg/bin-locations-list/"]
    no_refs = True

    def parse(self, response):
        for row in response.xpath('//div[@class="post-content"]//tbody//tr'):
            name = row.xpath("./td[2]/text()").get()
            coords = row.xpath("./td[3]/text()").get().split(",")

            item = {
                "name": name,
                "lat": coords[0],
                "lon": coords[1],
            }
            yield Feature(**item)
