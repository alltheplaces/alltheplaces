from locations.spiders.kia_au import KiaAUSpider


class KiaFJSpider(KiaAUSpider):
    name = "kia_fj"
    start_urls = ["https://www.kia.com/api/kia_fiji/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def post_process_feature(self, item, feature):
        item["phone"] = item["phone"].split("&", 1)[0].strip()
        yield item
