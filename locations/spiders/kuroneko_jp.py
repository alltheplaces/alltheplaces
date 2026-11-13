import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana


class KuronekoJPSpider(Spider):
    name = "kuroneko_jp"
    allowed_domains = ["locations2.kuronekoyamato.co.jp"]

    skip_names = [
        "ツルハ",
        "福太郎",
        "イレブン",
        "ウォンツ",
        "B＆D",
        "Ｂ＆D",
    ]

    async def start(self):
        for lat, lon in country_iseadgg_centroids("JP", 24):
            yield Request(
                "https://locations2.kuronekoyamato.co.jp/api/v1/stores/nearsearch"
                f"?site=yamato01&lat={lat}&lon={lon}&search_range=24&disp_cnt=5000&store_yamato=1&store_other=1",
                callback=self.parse,
            )

    def parse(self, response):
        data = response.json()
        for store in data["store_datasets"]:
            if any(token in store["shop_nm"] for token in self.skip_names):
                continue

            item = Feature()
            item["ref"] = store["kyoten_id"]
            item["lat"] = store["wgs_lat"]
            item["lon"] = store["wgs_lon"]
            item["addr_full"] = store["shop_addr"]
            item["website"] = f"https://locations2.kuronekoyamato.co.jp/yamato01/Detail?id={store['kyoten_id']}"

            if store["shop_type_cd"] == "1":
                branch = re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", store["shop_nm"])
                apply_category(Categories.POST_OFFICE, item)
                item["branch"] = branch
                item["name"] = item["brand"] = "ヤマト運輸"
                item["brand_wikidata"] = "Q6584353"
                item.set_tag("post_office:parcel_from", "yes")
                item.set_tag("post_office:parcel_to", "yes")
                item.set_tag("post_office:parcel_pickup", "yes")

            else:
                item["name"] = store["shop_nm"]
                apply_category(Categories.GENERIC_POI, item)
                item.set_tag("post_office", "post_partner")
                item.set_tag("post_office:service_provider", "ヤマト運輸")
                item.set_tag("post_office:brand", "ヤマト運輸")
                item.set_tag("post_office:brand:wikidata", "Q6584353")
                item.set_tag("post_office:parcel_from", "yes")
                item.set_tag("post_office:parcel_to", "yes")

            oh = OpeningHours()
            for day in DAYS_3_LETTERS:
                prefix = day.lower()
                if store[f"{prefix}_cl_flg"] == "1":
                    oh.set_closed(day)
                    continue
                op = store[f"{prefix}_op_tm"]
                cl = store[f"{prefix}_cl_tm"]
                if op and cl:
                    oh.add_range(
                        day,
                        f"{op[:2]}:{op[2:]}",
                        f"{cl[:2]}:{cl[2:]}",
                    )
            item["opening_hours"] = oh

            detail_url = "https://locations2.kuronekoyamato.co.jp/api/v1/stores/" f"{store['kyoten_id']}?site=yamato01"
            yield Request(detail_url, callback=self.parse_detail, cb_kwargs={"item": item})

    def parse_detail(self, response, item):
        detail = response.json()
        item["postcode"] = detail.get("zip_num")
        if detail.get("tel_num"):
            item["phone"] = detail["tel_num"]
        if detail.get("parking_flg") == "1":
            item.set_tag("parking", "yes")
            if detail.get("parking_cap") is not None:
                item.set_tag("parking:capacity:standard", detail["parking_cap"])
        kn = detail.get("shop_kn_nm")
        if kn:
            cleaned = re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", kn)
            hira = katakana_to_hiragana(cleaned)
            if "branch" in item:
                item.set_tag("branch:ja-Hira", hira)
            else:
                item.set_tag("name:ja-Hira", hira)
        yield item
