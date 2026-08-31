import csv
from io import StringIO

from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature

MAX_ITEMS = 1640  # determined experimentally
RADIUS_KM = 24
MAP_ID = "lbankatm"


class LawsonBankJPSpider(Spider):
    name = "lawson_bank_jp"
    item_attributes = {
        "brand": "ローソン銀行",
        "brand_wikidata": "Q11350963",
    }

    def make_request(self, lat, lon, offset=1, count=900):
        radius_m = RADIUS_KM * 1000
        return Request(
            f"https://map.lawsonbank.jp/p/{MAP_ID}/zdcemaphttp.cgi?target=http%3A%2F%2F127.0.0.1%2Fcgi%2Fnkyoten.cgi%3F%26cid%3D{MAP_ID}%26pos%3D{offset}%26lat%3D{lat}%26lon%3D{lon}%26knsu%3D{MAX_ITEMS}%26cnt%3D{count}%26hour%3D1%26rad%3D{radius_m}&zdccnt=1",
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
            item["website"] = f"https://map.lawsonbank.jp/p/{MAP_ID}/dtl/{row[0]}/"
            item["lat"] = row[1]
            item["lon"] = row[2]
            item["branch"] = row[7].removeprefix("ローソン銀行ＡＴＭ　").removesuffix("共同出張所")
            item["addr_full"] = row[8]

            apply_category(Categories.ATM, item)

            yield item
