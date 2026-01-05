from scrapy import Spider

from locations.items import Feature


class MadameFrigoCHSpider(Spider):
    name = "madame_frigo_ch"
    item_attributes = {"brand": "Madame Frigo", "brand_wikidata": "Q122664134"}
    start_urls = ["https://www.madamefrigo.ch/en/locations/"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@id="maps-pins"]/div[@class="fridge"]'):
            item = Feature()
            item["ref"] = location.xpath("./@id").get()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["branch"] = location.xpath('.//p[@class="hyphenate"]/text()').get()

            yield item
