from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class LaTaverneTableDeCaractereFRSpider(Spider):
    name = "la_taverne_table_de_caractere_fr"
    item_attributes = {"brand": "La Taverne - Table de Caractère", "brand_wikidata": "Q141215923"}
    start_urls = ["https://www.lestavernes.com/nos-restaurants-la-taverne-table-de-caracteres/"]

    def parse(self, response, **kwargs):
        for li in response.xpath('//ul[contains(@class, "wpv-loop")]/li'):
            marker = li.xpath('preceding-sibling::div[contains(@class, "js-wpv-addon-maps-marker")][1]')
            website = li.xpath(".//a/@href").get()

            item = Feature()
            item["ref"] = website.strip("/").rsplit("/", 1)[-1]
            item["website"] = website
            item["branch"] = li.xpath('.//div[@class="nom-restaurant"]/text()').get("").strip()
            item["street_address"] = li.xpath('.//div[@class="adresse-restaurant"]/text()').get("").strip()
            item["postcode"] = li.xpath('.//div[@class="code_postal-restaurant"]/text()').get("").strip()
            item["city"] = (
                li.xpath('.//div[@class="code_postal-restaurant"]/following-sibling::div/text()').get("").strip()
            )
            item["phone"] = li.xpath('.//div[@class="tel-restaurant"]/text()').get()
            item["email"] = li.xpath('.//div[@class="mail-restaurant"]//a/@href').get("").replace("mailto:", "")
            item["lat"] = marker.xpath("@data-markerlat").get()
            item["lon"] = marker.xpath("@data-markerlon").get()

            # A couple of locations have the postcode merged into the city field on the source page.
            if item["city"][:5].isdigit():
                item["postcode"], item["city"] = item["city"][:5], item["city"][5:].strip()

            apply_category(Categories.RESTAURANT, item)
            yield item
