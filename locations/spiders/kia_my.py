import re

from locations.spiders.kia_au import KiaAUSpider


class KiaMYSpider(KiaAUSpider):
    name = "kia_my"
    start_urls = ["https://www.kia.com/api/kia_malaysia/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def post_process_feature(self, item, feature):
        item["email"] = item["email"].splitlines()[0].strip()
        item["phone"] = re.sub(r"[^\d\- ]+", "", item["phone"].splitlines()[0].strip())
        yield item
