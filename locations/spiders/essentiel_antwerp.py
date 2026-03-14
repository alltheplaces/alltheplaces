from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class EssentielAntwerpSpider(AlgoliaSpider):
    name = "essentiel_antwerp"
    item_attributes = {"brand": "Essentiel Antwerp", "brand_wikidata": "Q117456339"}
    # Found in JS bundle: /_next/static/chunks/8962-*.js, module 3527 (app config)
    app_id = "DEA7SC4GE0"
    api_key = "1be00bba6480d955bdf9ac166b8f1471"
    index_name = "ea_live_storelocator_stores"
    LANG_STOREFRONTS = {"nl": "be_nl", "fr": "fr_fr", "de": "de_de", "es": "es_es", "it": "it_it", "en": "be_en"}
    COUNTRY_STOREFRONT = {
        "BE": "be_nl",
        "NL": "nl_nl",
        "DE": "de_de",
        "FR": "fr_fr",
        "IT": "it_it",
        "ES": "es_es",
        "UK": "uk",
        "US": "us",
    }
    COUNTRY_LANG = {"BE": "nl", "NL": "nl", "DE": "de", "FR": "fr", "IT": "it", "ES": "es", "UK": "en", "US": "en"}

    def pre_process_data(self, feature: dict) -> None:
        feature["street_address"] = feature.pop("streetandnumber", None)
        feature["ref"] = feature.pop("storecode", None)
        feature["_store_name_translations"] = feature.pop("storeName", {})
        lang = self.COUNTRY_LANG.get(feature.get("countryCode"), "en")
        feature["_lang"] = lang
        feature["city"] = feature.pop("city", {}).get(lang) or ""
        feature["coordinates"] = feature.pop("_geoloc", {})

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not feature.get("visible"):
            return

        translations = feature["_store_name_translations"]
        item["branch"] = translations.get(feature["_lang"]) or translations.get("en", "")

        slug = feature["slug"]
        for lang, name in translations.items():
            item["extras"][f"branch:{lang}"] = name
            if lang in self.LANG_STOREFRONTS:
                item["extras"][
                    f"website:{lang}"
                ] = f"https://www.essentiel-antwerp.com/{self.LANG_STOREFRONTS[lang]}/stores/{slug}"

        storefront = self.COUNTRY_STOREFRONT.get(feature.get("countryCode"), "be_en")
        item["website"] = f"https://www.essentiel-antwerp.com/{storefront}/stores/{slug}"
        item["opening_hours"] = self.parse_hours(feature)

        yield item

    @staticmethod
    def parse_hours(store: dict) -> OpeningHours | None:
        oh = OpeningHours()
        try:
            for day in DAYS_FULL:
                open_time = store.get(f"{day.lower()}Open")
                close_time = store.get(f"{day.lower()}Close")
                if open_time and close_time:
                    oh.add_range(day[:2], open_time, close_time)
        except Exception:
            return None
        return oh
