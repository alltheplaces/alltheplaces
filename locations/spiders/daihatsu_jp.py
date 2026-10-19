import re
import unicodedata
from typing import Iterable

from pyproj import Transformer
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# The shop pages give coordinates in the Tokyo datum, about 450 m off from WGS 84.
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")
LIST_URL = "https://map.daihatsu.co.jp/search/shop/shop_list/?carTypeCode=195&btnMenu=1%2C2%2C4%2C5%2C3&page={}"


class DaihatsuJPSpider(Spider):
    name = "daihatsu_jp"
    item_attributes = {"brand": "ダイハツ", "brand_wikidata": "Q27511"}
    allowed_domains = ["map.daihatsu.co.jp"]
    start_urls = [LIST_URL.format(1)]

    def parse(self, response: Response, page: int = 1) -> Iterable[Request]:
        # Without a search point the list holds every shop in the country, 10 per page.
        for link in response.xpath('//li[@class="shopName"]/a/@href').getall():
            yield response.follow(link, callback=self.parse_shop)
        if m := re.search(r"(\d+)件中", response.text):
            if page * 10 < int(m.group(1)):
                yield Request(LIST_URL.format(page + 1), cb_kwargs={"page": page + 1})

    def parse_shop(self, response: Response) -> Iterable[Feature]:
        js = {k: v for k, v in re.findall(r"var (\w+) = \"?([^\";]*)\"?;", response.text)}
        new_car = js.get("new_car_flg") == "1"
        used_car = js.get("old_car_flg") == "1"
        service = js.get("service_factory_flg") == "1"
        branch = js.get("tempo_name", "").replace("\u3000", " ")
        if "法人" in branch or "閉店" in branch:
            return  # corporate sales teams, and shops marked as closed
        if branch == "本社" and not (new_car or used_car or service):
            return  # head office without a showroom

        item = Feature()
        hansha = re.search(r"hanshaCode=(\w+)", response.url).group(1)
        tenpo = re.search(r"tenpoCode=(\w+)", response.url).group(1)
        item["ref"] = f"{hansha}-{tenpo}"
        # "ダイハツショップ" are smaller dealers run by local garages under contract
        # to the regional sales company, so that company is not their operator.
        if not branch.startswith("ダイハツショップ"):
            item["operator"] = js.get("hansya_name")
        # Drop the dealer type prefix and notes like "(直営店)" or "※リニューアルオープン予定"
        branch = re.sub(r"^ダイハツショップ店?\s*|\s*※.*|[(（]直営店[)）]", "", branch)
        item["branch"] = branch.strip()
        item["website"] = response.url
        item["addr_full"] = response.xpath('//dd[contains(@class, "shopAddress")]/text()').get("").strip()
        item["phone"] = response.xpath('//dd[contains(@class, "shopTel")]//a/text()').get()
        item["extras"]["fax"] = self.info(response, "FAX")
        if m := re.search(r"L\.latLng\(([\d.]+),\s*([\d.]+)\)", response.text):
            item["lat"], item["lon"] = TOKYO_TO_WGS84.transform(float(m[1]), float(m[2]))
        item["opening_hours"] = self.parse_hours(self.info(response, "営業時間"), self.info(response, "休日"))

        if new_car or used_car or not service:
            # Smaller "ダイハツショップ" dealers list no services at all; they sell cars.
            sales = item.deepcopy()
            sales["ref"] = f"{item['ref']}-sales"
            apply_category(Categories.SHOP_CAR, sales)
            apply_yes_no(Extras.VEHICLE_NEW_CAR_SALES, sales, new_car)
            apply_yes_no(Extras.VEHICLE_USED_CAR_SALES, sales, used_car)
            yield sales
        if service:
            repair = item.deepcopy()
            repair["ref"] = f"{item['ref']}-service"
            apply_category(Categories.SHOP_CAR_REPAIR, repair)
            yield repair

    @staticmethod
    def info(response: Response, title: str) -> str | None:
        text = response.xpath(f'//dt[@class="basicInfo__title"][text()="{title}"]/following-sibling::dd[1]//text()')
        value = " ".join(t.strip() for t in text.getall() if t.strip())
        return value or None

    @staticmethod
    def parse_hours(hours: str | None, closed: str | None) -> OpeningHours | None:
        # Hours and closing days are free text written by each dealer. Only the simple
        # cases are kept: one daily time range, and closing days that repeat every week.
        if not hours or not closed:
            return None
        hours = unicodedata.normalize("NFKC", hours)
        closed = unicodedata.normalize("NFKC", closed)

        if re.search(r"[月火水木金土日](?:曜|・|〜|~|-)|平日|土日|祝", hours):
            return None  # different hours on different days
        # Notes such as "(サービス受付17:30まで)" are about the workshop's last intake.
        hours = re.sub(r"\(.*?\)|【.*?】", "", hours)
        hours = re.sub(r"午後(\d{1,2})", lambda m: str(int(m.group(1)) % 12 + 12), hours).replace("午前", "")
        ranges = set(re.findall(r"(\d{1,2})(?::|時)(\d{2})?分?\s*[〜~∼ー−-]\s*(\d{1,2})(?::|時)(\d{2})?", hours))
        if len(ranges) != 1:
            return None
        open_h, open_m, close_h, close_m = ranges.pop()
        open_time = f"{int(open_h):02d}:{open_m or '00'}"
        close_time = f"{int(close_h):02d}:{close_m or '00'}"

        # Yearly holidays (New Year, Golden Week, summer) are left out.
        if re.search(r"第|隔週|不定|一部|カレンダー|祝|変更|異な|指定|追加|\d回", closed):
            return None  # closed on some weeks only, or on dates we don't have
        closed = re.sub(r"\(.*?\)|【.*?】", "", closed)
        # e.g. "毎週月〜水曜日" becomes "毎週月・火・水曜日"
        closed = re.sub(
            r"([月火水木金土日])曜?日?\s*[〜~ー−-]\s*([月火水木金土日])",
            lambda m: "・".join("月火水木金土日"["月火水木金土日".index(m[1]) : "月火水木金土日".index(m[2]) + 1]),
            closed,
        )
        # e.g. "毎週月・火曜日", "毎週月曜日、火曜日"
        named = "".join(re.findall(r"(?<!曜)((?:[月火水木金土日][・、]?)+)曜", closed))
        closed_days = {DAYS[i] for i, d in enumerate("月火水木金土日") if d in named}
        if not closed_days and "無休" not in closed:
            return None

        oh = OpeningHours()
        for day in DAYS:
            if day not in closed_days:
                oh.add_range(day, open_time, close_time)
        return oh
