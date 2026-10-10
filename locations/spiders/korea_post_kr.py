import re
from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

KOREA_POST = {"operator": "우정사업본부", "operator_wikidata": "Q483280"}

# Mail sorting and delivery centres and the postal museum are listed among the post offices
# but have no public counter.
NON_PUBLIC = re.compile(r"우편집중국|물류센터|집배센터|우정박물관")
SUSPENDED = re.compile(r"업무중지")
TIME_RANGE = re.compile(r"(\d{1,2}:\d{2})\s*[~-]\s*(\d{1,2}:\d{2})")
SATURDAY_RANGE = re.compile(r"토\D*(\d{1,2}:\d{2})\s*[~-]\s*(\d{1,2}:\d{2})")
# Collection times are free text: "10:00", "09;00", "16:.30", "10시", "16시30분", "오전 11시", "오후 3시".
COLLECTION_TIME = re.compile(r"(오전|오후)?\s*(\d{1,2})\s*(?:시\s*(?:(\d{1,2})\s*분)?|[:;.]+\s*(\d{2}))")


class KoreaPostKRSpider(Spider):
    name = "korea_post_kr"
    allowed_domains = ["www.koreapost.go.kr"]

    # The locator's nearby search ("우체국/우체통찾기") accepts any radius and is not capped, so one query
    # around the middle of the country returns every post office or post box.
    CENTRE = (35.9, 127.8)
    RADIUS_KM = 500
    # searchFacil: 1 = 우체국 (post offices, incl. agencies), 2 = 우체통 (post boxes).
    # 3 = 365 corners (ATMs), 4 = unmanned kiosks and 5 = stamp vendors are not collected.
    FACILITIES = ("1", "2")

    async def start(self) -> AsyncIterator[FormRequest]:
        for facility in self.FACILITIES:
            yield FormRequest(
                "https://www.koreapost.go.kr/extra/user/searchNearMap.do",
                formdata={
                    "searchFacil": facility,
                    "KPOST_LATITUDE": str(self.CENTRE[0]),
                    "KPOST_LONGITUDE": str(self.CENTRE[1]),
                    "searchGap": str(self.RADIUS_KM),
                    "searchExtraBusiness": "",
                    "searchExtraBusinessTerms": "",
                },
                # Without this header the endpoint redirects to an error page.
                headers={"X-Requested-With": "XMLHttpRequest"},
                callback=self.parse_list,
            )

    def parse_list(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["searchNearMap"]:
            if location["postDiv"] not in ("post", "box"):
                continue
            if location["postDiv"] == "post":
                if SUSPENDED.search(location["postNm"]):
                    self.crawler.stats.inc_value("atp/korea_post_kr/suspended")
                    continue
                if NON_PUBLIC.search(location["postNm"]):
                    self.crawler.stats.inc_value("atp/korea_post_kr/non_public")
                    continue
            yield response.follow(
                "/extra/user/{}/gps/searchMapInfo.do".format(location["postId"]),
                callback=self.parse_location,
                cb_kwargs={"location": location},
            )

    def parse_location(self, response: Response, location: dict) -> Any:
        details = {}
        for dt in response.xpath('//dl[@id="info-traffic"]/dt'):
            key = re.sub(r"\s+", "", dt.xpath("string(.)").get())
            dd = dt.xpath("following-sibling::dd[1]")
            details[key] = dd

        item = Feature()
        item["ref"] = str(location["postId"])
        item["lat"] = location["postLat"].strip()
        item["lon"] = location["postLon"].strip()

        if address := details.get("주소"):
            lines = [line.strip(" :\t\r\n") for line in address.xpath("text()").getall()]
            lines = [line for line in lines if line]
            if lines:
                item["addr_full"] = clean_address(lines[0])
            if len(lines) > 1:
                if postcode := re.search(r"zipcode:\s*(\d{5})", lines[1]):
                    item["postcode"] = postcode.group(1)

        if location["postDiv"] == "box":
            apply_category(Categories.POST_BOX, item)
            item.update(KOREA_POST)
            if place := details.get("상세위치"):
                if description := self.text(place):
                    item["extras"]["description"] = description
            if times := details.get("수집시간"):
                if collection_times := self.parse_collection_times(self.text(times)):
                    item["extras"]["collection_times"] = collection_times
            # Eco post boxes ("에코우체통") also accept small parcels.
            apply_yes_no(Extras.PARCEL_MAIL_IN, item, ",3," in (location.get("postExtraBusiness") or ""))
            yield item
            return

        name = re.sub(r"\s*[(\[].*?[)\]]\s*", "", location["postNm"]).strip(" -")
        item["name"] = name
        if name_en := (location.get("postNmEn") or "").strip():
            item["extras"]["name:en"] = name_en
        if phone := details.get("전화"):
            item["phone"] = self.text(phone)
        # The "홈페이지" link goes to the supervising district post office, not to this location.
        item["website"] = response.url
        if hours := details.get("우편영업시간"):
            if "토" in self.text(hours):
                self.crawler.stats.inc_value("atp/korea_post_kr/saturday_hours")
                self.logger.info(f"Saturday hours for {location['postId']}: {self.text(hours)}")
            lunch = details.get("점심시간휴무제")
            item["opening_hours"] = self.parse_opening_hours(self.text(hours), self.text(lunch) if lunch else "")

        if "취급국" in name:
            # 우편취급국 are post office agencies run by private contractors.
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = KOREA_POST["operator"]
            item["extras"]["post_office:brand:wikidata"] = KOREA_POST["operator_wikidata"]
        else:
            apply_category(Categories.POST_OFFICE, item)
            item.update(KOREA_POST)
        yield item

    @staticmethod
    def text(selector) -> str:
        return re.sub(r"\s+", " ", selector.xpath("string(.)").get()).strip(" :")

    @staticmethod
    def parse_collection_times(text: str) -> str | None:
        times = set()
        for meridiem, hour, minute_ko, minute in COLLECTION_TIME.findall(text):
            hour, minute = int(hour), int(minute or minute_ko or 0)
            if meridiem == "오후" and hour < 12:
                hour += 12
            if hour < 24 and minute < 60:
                times.add(f"{hour:02d}:{minute:02d}")
        if not times:
            return None
        # Korea Post collects from post boxes on weekdays only.
        return "Mo-Fr {}".format(",".join(sorted(times)))

    @staticmethod
    def parse_opening_hours(text: str, lunch: str) -> OpeningHours | None:
        if not (match := TIME_RANGE.search(text)):
            return None
        open_time, close_time = (t.zfill(5) for t in match.groups())
        oh = OpeningHours()
        # Post offices open Monday to Friday; the locator lists one set of weekday hours.
        lunch_break = TIME_RANGE.search(lunch)
        if lunch_break and open_time < lunch_break.group(1).zfill(5) < close_time:
            oh.add_days_range(DAYS_WEEKDAY, open_time, lunch_break.group(1).zfill(5))
            oh.add_days_range(DAYS_WEEKDAY, lunch_break.group(2).zfill(5), close_time)
        else:
            oh.add_days_range(DAYS_WEEKDAY, open_time, close_time)
        # A few offices add Saturday hours, e.g. "09:00~18:00 (토 09:00~13:00)".
        if saturday := SATURDAY_RANGE.search(text):
            oh.add_range("Sa", *(t.zfill(5) for t in saturday.groups()))
            oh.set_closed("Su")
        else:
            oh.set_closed(["Sa", "Su"])
        return oh
