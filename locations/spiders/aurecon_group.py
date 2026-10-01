import scrapy

from locations.categories import apply_category
from locations.items import Feature


class AureconGroupSpider(scrapy.Spider):
    name = "aurecon_group"
    item_attributes = {
        "brand": "Aurecon",
        "brand_wikidata": "Q2871849",
    }
    allowed_domains = ["www.aurecon.com", "www.aurecongroup.com"]
    start_urls = ("https://www.aurecongroup.com/locations",)

    def parse(self, response):
        for location in response.xpath(".//h4"):
            addr = location.xpath(".//following-sibling::div")[0].xpath(".//div/span/following-sibling::div")[0]
            addr = " ".join(
                [
                    addr.xpath(".//span/text()").getall()[i].replace("\t", "").replace("\n", "").replace("\r", "")
                    for i in range(2)
                ]
            )
            coordinates = location.xpath('.//following-sibling::div//a[@target="_blank"]/@href').get()
            properties = {
                "ref": location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()').get().strip(),
                "brand": "Aurecon Group",
                "city": location.xpath(".//strong/text()").get().replace("\t", "").replace("\n", "").replace("\r", ""),
                "addr_full": addr,
                "phone": location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()').get().strip(),
            }
            if coordinates:
                coordinates = (str(coordinates).split("=")[1]).split(",")
                properties["lat"] = float(coordinates[0])
                properties["lon"] = float(coordinates[1])
            apply_category({"office": "construction_company"}, properties)
            yield Feature(**properties)
