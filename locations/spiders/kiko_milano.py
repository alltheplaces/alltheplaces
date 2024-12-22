from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class KikoMilanoSpider(JSONBlobSpider):
    name = "kiko_milano"
    item_attributes = {"brand": "KIKO Milano", "brand_wikidata": "Q3812045"}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield JsonRequest(
            url="https://api.retailtune.com/storelocator/v1/stores/get",
            data={"language": "en"},
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer 0WNG4nqY725RhWGuaIjlPq8T2NnPxcRwNr1I1Oe4C6pJrrHomfslKXzLpgZKT02y6W0yKnc2SC4",
                "Origin": "https://kiko-stores.kikocosmetics.com",
                "Referer": "https://kiko-stores.kikocosmetics.com/",
            },
        )
