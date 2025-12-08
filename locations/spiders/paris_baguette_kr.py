from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature


class ParisBaguetteKRSpider(Spider):
    name = "paris_baguette_kr"
    item_attributes = {"brand": "파리바게뜨", "brand_wikidata": "Q62605260"}
    start_urls = ["https://www.paris.co.kr/wp-admin/admin-ajax.php?action=pb_store_get_area"]

    def parse(self, response):
        for state in response.json().values():
            if "id" in state:
                yield Request(
                    f"https://www.paris.co.kr/wp-admin/admin-ajax.php?action=pb_store_get_list&type=%23search&area1={state['id']}",
                    callback=self.parse_stores,
                    cb_kwargs={"state": state["name"]},
                )

    def parse_stores(self, response, state=None):
        for location in response.xpath("//li"):
            item = Feature()
            item["state"] = state
            item["ref"] = location.xpath("div/@data-id").get()
            item["lat"] = location.xpath("div/@data-latitude").get()
            item["lon"] = location.xpath("div/@data-longitude").get()
            item["branch"] = location.xpath(".//h3[@class='store-name']/span/text()").get()
            item["addr_full"] = location.xpath(".//p[@class='store-addr']/text()").get()
            item["phone"] = location.xpath(".//a[@class='tel']/text()").get()
            item["website"] = f"https://www.paris.co.kr/store-detail/?id={item['ref']}"
            apply_yes_no(Extras.DELIVERY, item, bool(location.xpath(".//i[@class='delivery']")))
            yield item
