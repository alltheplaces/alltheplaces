from urllib.parse import urljoin

from scrapy import Selector, Spider

from locations.items import Feature


class KreatosBESpider(Spider):
    name = "kreatos_be"
    item_attributes = {"brand": "Kreatos", "brand_wikidata": "Q113540702"}
    start_urls = ["https://www.kreatos.be/store-locator/json"]

    def parse(self, response, **kwargs):
        for location in response.json()["features"]:
            item = Feature()
            item["geometry"] = location["geometry"]
            item["name"] = location["properties"]["name"]
            item["ref"] = str(location["properties"]["Nid"])

            sel = Selector(text=location["properties"]["description"])

            item["street"] = sel.xpath('//*[@class="thoroughfare"]/text()').get()
            item["housenumber"] = sel.xpath('//*[@class="premise"]/text()').get()
            item["city"] = sel.xpath('//span[@class="locality"]/text()').get()
            item["postcode"] = sel.xpath('//span[@class="postal-code"]/text()').get()
            item["country"] = sel.xpath('//span[@class="locality"]/text()').get()

            item["website"] = urljoin(
                response.url, Selector(text=location["properties"]["gsl_props_misc_rendered"]).xpath("//a/@href").get()
            )

            yield item
