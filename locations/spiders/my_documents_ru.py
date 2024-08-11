import scrapy

from locations.items import Feature


class MyDocumentsRUSpider(scrapy.Spider):
    name = "my_documents_ru"
    start_urls = ["https://xn--d1achjhdicc8bh4h.xn--p1ai/search/mfc"]
    item_attributes = {"brand": "Мои документы", "brand_wikidata": "Q57449742"}

    def parse(self, response):
        subjects = response.xpath('//select[@name="subjectId"]/option/@value').getall()
        for subject in subjects:
            yield scrapy.FormRequest(
                url="https://xn--d1achjhdicc8bh4h.xn--p1ai/search/mfc/mapJson",
                formdata={"page": "1", "subjectId": subject, "regionId": str(0), "serviceId": ""},
                callback=self.parse_pois,
                meta={"subject": subject},
            )

    def parse_pois(self, response):
        for poi in response.json()["features"]:
            item = Feature()
            item["ref"] = f"{poi['id']}-{response.meta['subject']}"
            item["lat"] = poi.get("geometry").get("coordinates")[0]
            item["lon"] = poi.get("geometry").get("coordinates")[1]
            item["name"] = poi["properties"]["hintContent"]
            baloonContent = poi["properties"]["balloonContentBody"]
            address, phone = baloonContent.split("</br>")
            item["addr_full"] = address
            item["country"] = "RU"
            item["phone"] = phone
            yield item
