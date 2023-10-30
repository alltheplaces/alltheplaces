from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ElClubDeLaMilanesaARSpider(WPStoreLocatorSpider):
    name = "el_club_de_la_milanesa_ar"
    item_attributes = {"brand": "El Club de la Milanesa", "brand_wikidata": "Q117324078"}
    allowed_domains = ["elclubdelamilanesa.com"]
    start_urls = ["https://elclubdelamilanesa.com/cdm-panel/admin-ajax.php?action=store_search&autoload=true"]

    def parse_item(self, item, location):
        item.pop("website", None)
        yield item
