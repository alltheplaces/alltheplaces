import csv
from io import StringIO

from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

BRANDS = {
    "1": ("LAWSON", "Q1557223"),
    "2": ("NATURAL LAWSON", "Q11323850"),
    "4": ("LAWSON STORE 100", "Q11350960"),
}
MAX_ITEMS = 1640  # determined experimentally
RADIUS_KM = 24


class LawsonJPSpider(Spider):
    name = "lawson_jp"
    item_attributes = {
        "brand": "LAWSON",
        "brand_wikidata": "Q1557223",
    }

    def make_request(self, lat, lon, offset=1, count=900):
        radius_m = RADIUS_KM * 1000
        return Request(
            f"https://www.e-map.ne.jp/p/lawson/zdcemaphttp.cgi?target=http%3A%2F%2F127.0.0.1%2Fcgi%2Fnkyoten.cgi%3F%26cid%3Dlawson%26pos%3D{offset}%26lat%3D{lat}%26lon%3D{lon}%26knsu%3D{MAX_ITEMS}%26cnt%3D{count}%26hour%3D1%26rad%3D{radius_m}&zdccnt=1",
            cb_kwargs={"lat": lat, "lon": lon, "offset": offset},
        )

    async def start(self):
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon)

    def parse(self, response, lat, lon, offset):
        # response is an EUC-encoded JS file that looks like
        #   ZdcEmapHttpResult[1] = '...';
        # where the string body is a TSV
        js_body = response.body.decode("euc-jp")
        # chompjs sees the array index as an array itself, so get just the string itself:
        js_str = js_body[js_body.find("'") : js_body.rfind("'") + 1]
        # For some reason, neither Python json nor chompjs like just the string on its own, so wrap it in an array
        js_ls = f"[{js_str}]"
        (tsv_str,) = parse_js_object(js_ls)
        reader = csv.reader(StringIO(tsv_str), delimiter="\t")
        ret_code, rec_count, hit_count = map(int, next(reader))
        assert rec_count <= hit_count, (rec_count, hit_count)
        if hit_count >= MAX_ITEMS:
            self.logger.warning("Maximum number of items returned in one query, consider lowering the radius")
        if rec_count >= hit_count:
            yield self.make_request(lat, lon, offset + rec_count)
        for row in reader:
            item = Feature()
            item["ref"] = row[0]
            item["website"] = f"https://www.e-map.ne.jp/p/lawson/dtl/{row[0]}/"
            item["lat"] = row[1]
            item["lon"] = row[2]
            item["brand"], item["brand_wikidata"] = BRANDS.get(row[3], (None, None))
            item["branch"] = row[6]
            item["addr_full"] = row[7]
            item["phone"] = row[8]
            if row[10] == "1":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, row[11], row[12])

            apply_yes_no(Extras.ATM, item, row[13] in ("1", "2"))
            apply_yes_no("parking", item, row[39] == "1")
            apply_yes_no(Fuel.ELECTRIC, item, row[28] == "1")
            apply_yes_no(PaymentMethods.CONTACTLESS, item, row[45] == "1")
            apply_yes_no(Extras.INDOOR_SEATING, item, row[43] == "1")
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, row[44] == "1")

            apply_yes_no("drinks", item, row[14] == "1")
            apply_yes_no("food", item, row[28] == "1")
            apply_yes_no("books", item, row[42] == "1")
            apply_yes_no(Extras.HALAL, item, row[46] == "1")

            # TODO: delivery, COL_79
            apply_yes_no(Extras.PARCEL_MAIL_IN, item, row[49] == "1")
            apply_yes_no(Extras.COPYING, item, row[18] == "1")
            apply_yes_no("laundry_service", item, row[34] == "1")
            apply_yes_no("duty_free", item, row[47] == "1")
            # TODO: 移動販売 / "Mobile sales"

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
