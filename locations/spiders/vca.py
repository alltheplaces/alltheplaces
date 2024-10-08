import scrapy

from locations.linked_data_parser import LinkedDataParser


class VcaSpider(scrapy.Spider):
    name = "vca"
    item_attributes = {"brand": "VCA", "brand_wikidata": "Q7906620"}
    allowed_domains = ["vcahospitals.com"]
    start_urls = ("https://vcahospitals.com/find-a-hospital/location-directory",)

    def parse(self, response):
        urls = response.xpath('//span[@class="location-accordion__location-name"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        ld_item = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        ld_item["openingHours"] = ld_item.pop("openingHours")[0].split(", ")

        item = LinkedDataParser.parse_ld(ld_item)
        item["name"] = item.pop("name").strip("'")
        item["lat"] = item.pop("lat")[:-1]
        item["lon"] = item.pop("lon")[:-1]
        item["ref"] = response.url
        item["website"] = response.url
        yield item
