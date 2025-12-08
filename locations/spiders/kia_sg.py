from locations.categories import Categories, apply_category
from locations.spiders.kia_au import KiaAUSpider


class KiaSGSpider(KiaAUSpider):
    name = "kia_sg"
    start_urls = ["https://www.kia.com/api/kia_singapore/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def post_process_feature(self, item, feature):
        if feature["dealerNm"] == "test test":
            return
        if "Authorised Service Centre" in feature["dealerNm"]:
            item["extras"] = {}
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
