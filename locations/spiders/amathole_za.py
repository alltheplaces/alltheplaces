from scrapy import Spider

from locations.items import Feature


class AmatholeZASpider(Spider):
    name = "amathole_za"
    item_attributes = {"brand": "Amathole Funerals", "brand_wikidata": "Q122593900"}
    start_urls = ["https://amatholefunerals.co.za/contact.html"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[@class="about-text-box"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3/text()").get()
            info = location.xpath(".//p/text()").getall()
            for line in info:
                if line.strip()[0] == "0":
                    item["phone"] = line
                elif "@" in line:
                    item["email"] = line
                else:
                    item["street_address"] = line
            yield item
