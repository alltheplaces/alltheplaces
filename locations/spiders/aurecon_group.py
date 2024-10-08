import scrapy

from locations.items import Feature


class AureconGroupSpider(scrapy.Spider):
    name = "aurecon_group"
    item_attributes = {"brand": "Aurecon", "brand_wikidata": "Q2871849", "extras": {"office": "construction_company"}}
    allowed_domains = ["www.aurecon.com"]
    start_urls = ("https://www.aurecongroup.com/locations",)

    def parse(self, response):
        for location in response.xpath(".//h4"):
            addr = location.xpath(".//following-sibling::div")[0].xpath(".//div/span/following-sibling::div")[0]
            addr = " ".join(
                [
                    addr.xpath(".//span/text()").extract()[i].replace("\t", "").replace("\n", "").replace("\r", "")
                    for i in range(2)
                ]
            )
            coordinates = str(location.xpath('.//following-sibling::div//a[@target="_blank"]/@href').extract_first())
            properties = {
                "ref": location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()')
                .extract_first()
                .strip(),
                "brand": "Aurecon Group",
                "city": location.xpath(".//strong/text()")
                .extract_first()
                .replace("\t", "")
                .replace("\n", "")
                .replace("\r", ""),
                "addr_full": addr,
                "phone": location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()')
                .extract_first()
                .strip(),
            }
            if coordinates:
                coordinates = (coordinates.split("=")[1]).split(",")
                properties["lat"] = float(coordinates[0])
                properties["lon"] = float(coordinates[1])
            yield Feature(**properties)
