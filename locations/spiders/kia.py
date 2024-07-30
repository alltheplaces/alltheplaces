import scrapy

from locations.items import Feature


class KiaSpider(scrapy.Spider):
    name = "kia"
    item_attributes = {"brand": "Kia", "brand_wikidata": "Q35349"}
    start_urls = [
        f"https://www.kia.com/api/bin/dealer?locale={locale}&program=dealerLocatorSearch"
        for locale in [
            "at-de",
            "fr-fr",
            "de-de",
            "es-es",
            "nl-nl",
            "be-nl",
            "cz-cz",
            "dk-da",
            "fi-fi",
            "gr-el",
            "hu-hu",
            "ie-en",
            "it-it",
            "lu-fr",
            "no-nn",
            "se-sv",
            "pl-pl",
            "sk-sk",
        ]
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
