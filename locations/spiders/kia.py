import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
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
            phone = store.get("dealerPhone")
            item["phone"] = (
                phone.replace(";", "").replace(".", "").replace("/", "").replace(",", ";") if phone else None
            )
            email = store.get("dealerEmail")
            item["email"] = email.strip().strip(".").replace("@@", "@") if email else None
            if store.get("websiteUrl") not in ["None", "", "No Website", None]:
                website = store.get("websiteUrl").strip().replace("null", "")
                if website.startswith("www"):
                    website = "https://" + website
                elif website.startswith("kia"):
                    website = "https://www." + website
                item["website"] = website
            if not item.get("website"):
                item["website"] = "https://www.kia.com/"
            item["ref"] = store.get("dealerSeq")
            item["country"] = store.get("dealerCountry")
            dealer_type = store.get("dealerDealertype", "").lower()
            if "sales" in dealer_type:
                apply_category(Categories.SHOP_CAR, item)
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no("service:vehicle:car_repair", item, "service" in dealer_type)
            yield item
