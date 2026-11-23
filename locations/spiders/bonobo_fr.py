from locations.storefinders.beaumanoir import BeaumanoirSpider


class BonoboFRSpider(BeaumanoirSpider):
    name = "bonobo_fr"
    item_attributes = {"brand": "Bonobo", "brand_wikidata": "Q63682093", "name": "Bonobo"}
    start_urls = [
        "https://www.bonoboplanet.com/on/demandware.store/Sites-BNB_FR_SFRA-Site/fr_FR/Stores-FindStores?lat=46.6&long=2.4&radius=20000&showMap=false"
    ]
    # Cloudflare challenges plain requests.
    requires_proxy = "FR"

    def include_store(self, store: dict) -> bool:
        # The locator also lists multi-brand Vib's shops.
        return store["custom"]["BMNR_libBrand"] == "BONOBO"
