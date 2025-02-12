from locations.items import SocialMedia, set_social_media
from locations.storefinders.location_bank import LocationBankSpider


class CashCrusadersBWNAZASpider(LocationBankSpider):
    name = "cash_crusaders_bw_na_za"
    client_id = "37f1042e-52f8-42c9-adfc-71c3b878ffd4"
    item_attributes = {"brand": "Cash Crusaders", "brand_wikidata": "Q116895402"}

    def post_process_item(self, item, response, location):
        if ctas := location["callToAction"]:
            for cta in ctas:
                if "whatsapp" in cta["name"].lower():
                    if "=" in cta["url"]:
                        number = cta["url"].split("=")[1]
                    else:
                        number = cta["url"]
                    set_social_media(item, SocialMedia.WHATSAPP, number)
        yield item
