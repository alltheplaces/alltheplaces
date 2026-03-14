import scrapy

from locations.structured_data_spider import StructuredDataSpider


class ScsGBSpider(StructuredDataSpider):
    name = "scs_gb"
    item_attributes = {"brand": "ScS", "brand_wikidata": "Q19654399"}
    start_urls = ["https://www.scs.co.uk/stores/"]

    def parse(self, response):
        for link in response.xpath("//@href").extract():
            if link.startswith("/stores/"):
                yield scrapy.Request(url=response.urljoin(link), callback=self.parse_sd)
