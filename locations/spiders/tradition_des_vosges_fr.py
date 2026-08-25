# import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider

# from unidecode import unidecode


class TraditionDesVosgesFR(UberallSpider):
    name = "tradition_des_vosges_fr"
    item_attributes = {"brand": "Tradition des Vosges", "brand_wikidata": "Q141176147"}
    key = "xP2cflp47Y6iCF9r4vY35cJ99UvjpH"
    drop_attributes = ["image", "name"]

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        ### The website is broken, the link is correct but cannot be accessed directly, only from the store locator page
        # slug_city = re.sub(r"-+", "-", unidecode(re.sub(r"\W+", "-", item["city"].strip().lower())).replace(" ", "-"))
        # slug_address = re.sub(
        #     r"-+", "-", unidecode(re.sub(r"\W+", "-", item["street_address"].strip().lower())).replace(" ", "-")
        # )
        # slug_id = str(location["id"])
        # item["website"] = "https://www.traditiondesvosges.com/fr/magasins/l/{}/{}/{}".format(slug_city, slug_address, slug_id)

        apply_category(Categories.SHOP_HOUSEHOLD_LINEN, item)
        yield item
