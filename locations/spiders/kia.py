import scrapy

from locations.items import Feature


class KiaSpider(scrapy.Spider):
    name = "kia"
    item_attributes = {"brand": "Kia", "brand_wikidata": "Q35349"}
    start_urls = [
        "https://www.kia.com/api/bin/dealer?locale=at-de&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=fr-fr&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=de-de&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=es-es&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=nl-nl&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=be-nl&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=cz-cz&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=dk-da&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=fi-fi&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=gr-el&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=hu-hu&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=ie-en&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=it-it&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=lu-fr&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=no-nn&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=se-sv&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=pl-pl&program=dealerLocatorSearch",
        "https://www.kia.com/api/bin/dealer?locale=sk-sk&program=dealerLocatorSearch",
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["list"]:
            item = Feature()
            item["name"] = store.get("dealerName")
            item["street_address"] = store.get("dealerAddress")
            item["postcode"] = store.get("dealerPostcode")
            item["city"] = store.get("dealerResidence")
            item["lat"] = store.get("dealerLatitude")
            item["lon"] = store.get("dealerLongitude")
            item["phone"] = store.get("dealerPhone")
            item["email"] = store.get("dealerEmail")
            if store.get("websiteUrl") not in ["None", ""]:
                item["website"] = store.get("websiteUrl")
            else:
                item["website"] = "https://www.kia.com/"
            item["ref"] = store.get("dealerSeq")
            yield item
