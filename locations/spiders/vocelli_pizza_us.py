import urllib

from scrapy import FormRequest, Spider

from locations.items import Feature


class VocelliPizzaUSSpider(Spider):
    name = "vocelli_pizza_us"
    item_attributes = {"brand": "Vocelli Pizza", "brand_wikidata": "Q7939247"}
    start_urls = ["https://www.vocellipizza.com/Locations-amp-Offers"]

    def parse(self, response, **kwargs):
        for state in response.xpath('//select[@id="state"]/option/@value').getall():
            yield FormRequest(
                url="https://www.vocellipizza.com/Locations-amp-Offers",
                formdata={"state": state},
                callback=self.parse_state,
            )

    def parse_state(self, response, **kwargs):
        for location in response.xpath('//div[@class="location vcard"]'):
            item = Feature()
            item["ref"] = item["website"] = urllib.parse.urljoin(response.url, location.xpath("./nav//a/@href").get())
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-lon").get()
            item["name"] = location.xpath('.//div[@class="org"]/text()').get()
            item["street_address"] = location.xpath('.//span[@class="street-address"]/text()').get().strip()
            item["city"] = location.xpath('.//span[@class="locality"]/text()').get().strip()
            item["state"] = location.xpath('.//span[@class="region"]/text()').get().strip()
            item["postcode"] = location.xpath('.//span[@class="postal-code"]/text()').get()
            item["phone"] = location.xpath('.//span[@class="tel"]/text()').get()

            yield item
