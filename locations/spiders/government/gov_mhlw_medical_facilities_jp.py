import csv
import io
import re
import sys
import unicodedata
import zipfile
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_JP, OpeningHours
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana

# The source files use one character day names as column prefixes.
DAY_PREFIXES = [(prefix, day) for prefix, day in DAYS_JP.items() if len(prefix) == 1]

# Department codes to healthcare:speciality, from the mapping of the planned OSM import:
# https://github.com/nyampire/jp-healthcare-osm/blob/main/mapping/speciality_mapping.csv
SPECIALITIES = {
    "01001": "internal",
    "01002": "infectious_diseases",
    "01003": "venereology",
    "01004": "haematology;oncology",
    "01005": "haematology",
    "01006": "endocrinology",
    "01007": "endocrinology",
    "01008": "endocrinology",
    "01009": "endocrinology",
    "01010": "endocrinology",
    "01011": "endocrinology",
    "01012": "endocrinology",
    "01013": "neurology",
    "01014": "pulmonology",
    "01015": "geriatrics;pulmonology",
    "01016": "otolaryngology",
    "01017": "cardiology",
    "01018": "cardiology",
    "01019": "cardiology",
    "01020": "gastroenterology",
    "01021": "gastroenterology",
    "01022": "nephrology",
    "01023": "dialysis",
    "01024": "hepatology",
    "01025": "neurology",
    "01026": "oncology",
    "01027": "traditional_chinese_medicine",
    "01028": "geriatrics",
    "01029": "internal",
    "01030": "gastroenterology",
    "01031": "palliative",
    "01032": "anaesthetics",
    "01033": "allergology",
    "01034": "palliative",
    "01991": "internal",
    "02001": "surgery",
    "02002": "neurosurgery",
    "02003": "neurosurgery",
    "02004": "neurosurgery",
    "02005": "cardiothoracic_surgery",
    "02006": "surgery",
    "02007": "otolaryngology",
    "02008": "vascular_surgery",
    "02009": "cardiothoracic_surgery",
    "02010": "cardiothoracic_surgery",
    "02011": "cardiothoracic_surgery",
    "02012": "abdominal_surgery",
    "02014": "abdominal_surgery;transplant",
    "02015": "abdominal_surgery",
    "02016": "proctology",
    "02017": "urology",
    "02018": "abdominal_surgery",
    "02019": "abdominal_surgery",
    "02020": "abdominal_surgery",
    "02021": "abdominal_surgery",
    "02022": "surgery",
    "02023": "surgery",
    "02024": "surgery",
    "02025": "proctology",
    "02026": "proctology",
    "02027": "anaesthetics",
    "02028": "oncology",
    "02029": "otolaryngology",
    "02030": "cardiothoracic_surgery",
    "02031": "abdominal_surgery",
    "02032": "surgery",
    "02033": "transplant",
    "02034": "surgery;transplant",
    "02035": "orthopaedics",
    "02036": "plastic_surgery",
    "02037": "plastic_surgery",
    "02038": "palliative",
    "02991": "surgery",
    "03001": "paediatrics",
    "03002": "paediatrics;ophthalmology",
    "03003": "paediatrics;otolaryngology",
    "03004": "paediatrics;dermatology",
    "03005": "child_psychiatry",
    "03006": "paediatric_surgery",
    "03007": "paediatrics;urology",
    "03008": "neonatology",
    "03009": "paediatric_surgery;oncology",
    "03991": "paediatrics",
    "04001": "gynaecology",
    "04002": "gynaecology",
    "04003": "gynaecology",
    "04004": "gynaecology;fertility",
    "04991": "gynaecology",
    "05001": "ophthalmology",
    "05002": "otolaryngology",
    "05003": "otolaryngology",
    "05004": "otolaryngology",
    "05991": "ophthalmology",
    "05992": "otolaryngology",
    "06001": "dermatology",
    "06002": "dermatology",
    "06003": "dermatology;urology",
    "06004": "urology",
    "06005": "urology",
    "06006": "urology",
    "06007": "nephrology;urology",
    "06991": "dermatology",
    "06992": "urology",
    "07001": "psychiatry",
    "07002": "psychiatry",
    "07003": "psychiatry",
    "07004": "psychiatry;geriatrics",
    "07005": "psychiatry;geriatrics",
    "07991": "neuropsychiatry",
    "08001": "dentistry",
    "08002": "orthodontics",
    "08003": "dental_oral_maxillo_facial_surgery",
    "08004": "paediatric_dentistry",
    "08005": "orthodontics;paediatric_dentistry",
    "08991": "dental_oral_maxillo_facial_surgery",
    "09001": "allergology",
    "09002": "rheumatology",
    "09003": "physiatry",
    "09004": "radiology",
    "09005": "diagnostic_radiology",
    "09006": "radiotherapy",
    "09007": "radiotherapy",
    "09008": "pathology",
    "09009": "clinical_pathology",
    "09010": "emergency",
    "09011": "anaesthetics",
    "09991": "general",
}
# At dental clinics the "other" codes are mostly implants and cosmetic dentistry.
DENTAL_SPECIALITIES = SPECIALITIES | {"08991": "dentistry", "09991": "dentistry"}
EMERGENCY = "09010"


class GovMhlwMedicalFacilitiesJPSpider(Spider):
    """
    Medical facilities and pharmacies from the MHLW open data, released every 6 months.
    Department hours are merged into one opening_hours per facility, without the emergency department.
    """

    name = "gov_mhlw_medical_facilities_jp"
    start_urls = ["https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html"]
    allowed_domains = ["www.mhlw.go.jp"]
    dataset_attributes = {
        "attribution": "required",
        "attribution:name:ja": "厚生労働省 医療情報ネット",
        "attribution:name:en": "Ministry of Health, Labour and Welfare",
        "attribution:website": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html",
        "license": "Public Data License (Version 1.0)",
        "license:website": "https://www.digital.go.jp/resources/open_data/public_data_license_v1.0",
        "use:commercial": "permit",
    }
    tables = {
        "01-1_hospital_facility_info": ("parse_hospital", "01-2_hospital_speciality_hours"),
        "02-1_clinic_facility_info": ("parse_clinic", "02-2_clinic_speciality_hours"),
        "03-1_dental_facility_info": ("parse_dentist", "03-2_dental_speciality_hours"),
        "04_maternity_home": ("parse_maternity_home", None),
        "05_pharmacy": ("parse_pharmacy", None),
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for prefix, (callback, departments_prefix) in self.tables.items():
            cb_kwargs = {"callback": getattr(self, callback), "departments": {}}
            url = self.find_zip(response, prefix)
            if departments_prefix:
                yield response.follow(
                    self.find_zip(response, departments_prefix),
                    callback=self.parse_departments_zip,
                    cb_kwargs={"facilities_url": response.urljoin(url), "cb_kwargs": cb_kwargs},
                )
            else:
                yield response.follow(url, callback=self.parse_zip, cb_kwargs=cb_kwargs)

    @staticmethod
    def find_zip(response: Response, prefix: str) -> str:
        # The page lists every release, newest first.
        return response.xpath(f'//a[contains(@href, "/{prefix}_")][contains(@href, ".zip")]/@href').get()

    def parse_departments_zip(self, response: Response, facilities_url: str, cb_kwargs: dict) -> Any:
        departments = cb_kwargs["departments"]
        for row in read_zip(response):
            codes, hours = departments.setdefault(row["ID"], ([], [set() for _ in DAY_PREFIXES]))
            if (code := row["診療科目コード"]) not in codes:
                codes.append(code)
            if code == EMERGENCY:
                continue
            for day_hours, (day_ja, _) in zip(hours, DAY_PREFIXES):
                start = row[f"{day_ja}_診療開始時間"]
                end = row[f"{day_ja}_診療終了時間"]
                # Drop placeholder times such as 00:00-23:59 and 09:00-09:00.
                if start and end and "06:00" <= start < end <= "23:00":
                    day_hours.add((sys.intern(start), sys.intern(end)))
        yield Request(facilities_url, callback=self.parse_zip, cb_kwargs=cb_kwargs)

    def parse_zip(self, response: Response, callback, departments: dict) -> Iterable[Feature]:
        for row in read_zip(response):
            item = self.parse_common(row)
            yield from callback(item, row, departments.get(row["ID"]))

    def parse_common(self, row: dict) -> Feature:
        item = Feature()
        item["ref"] = row["ID"]
        # Missing coordinates are 0 and a few are placeholders with whole degrees such as 38, 140.
        lat, lon = row["所在地座標（緯度）"], row["所在地座標（経度）"]
        if "." in lat and "." in lon:
            item["lat"], item["lon"] = lat, lon
        item["addr_full"] = clean(row["所在地"])
        item["website"] = clean_website(row.get("案内用ホームページアドレス") or row.get("薬局のホームページアドレス"))

        item["name"] = clean(row.get("正式名称") or row.get("名称"))
        if kana := clean(row.get("正式名称（フリガナ）") or row.get("フリガナ")):
            item["extras"]["name:ja-Hira"] = katakana_to_hiragana(kana)
        if (short_name := clean(row.get("略称"))) and short_name != item["name"]:
            item["extras"]["short_name"] = short_name
        return item

    def parse_hospital(self, item: Feature, row: dict, departments: tuple | None) -> Iterable[Feature]:
        apply_category(Categories.HOSPITAL, item)
        set_beds(item, row)
        set_departments(item, row, departments, SPECIALITIES)
        yield item

    def parse_clinic(self, item: Feature, row: dict, departments: tuple | None) -> Iterable[Feature]:
        # Clinics with beds are amenity=clinic, the rest amenity=doctors.
        if set_beds(item, row):
            apply_category(Categories.CLINIC, item)
        else:
            apply_category(Categories.DOCTOR, item)
        set_departments(item, row, departments, SPECIALITIES)
        yield item

    def parse_dentist(self, item: Feature, row: dict, departments: tuple | None) -> Iterable[Feature]:
        apply_category(Categories.DENTIST, item)
        set_departments(item, row, departments, DENTAL_SPECIALITIES)
        yield item

    def parse_maternity_home(self, item: Feature, row: dict, departments: tuple | None) -> Iterable[Feature]:
        apply_category(Categories.BIRTHING_CENTRE, item)
        yield item

    def parse_pharmacy(self, item: Feature, row: dict, departments: tuple | None) -> Iterable[Feature]:
        apply_category(Categories.PHARMACY, item)
        item["extras"]["dispensing"] = "yes"
        item["opening_hours"] = parse_pharmacy_hours(row)
        yield item


def read_zip(response: Response) -> Iterable[dict]:
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        for file_name in archive.namelist():
            if not file_name.endswith(".csv"):
                continue
            with archive.open(file_name) as csv_file:
                yield from csv.DictReader(io.TextIOWrapper(csv_file, encoding="utf-8-sig"))


def clean(value: str | None) -> str | None:
    if value:
        return unicodedata.normalize("NFKC", value).strip() or None
    return None


def clean_website(value: str | None) -> str | None:
    if not (value := clean(value)):
        return None
    if re.fullmatch(r"https?://\S+", value):
        return value
    # Fix typos such as "http//", "htt://" and "//www", and bare domains.
    if m := re.fullmatch(r"(?:(https?|htt)?:?//)?([\w-]+(?:\.[\w-]+)+(?:[/?#]\S*)?)", value, flags=re.ASCII):
        return f"{'https' if m.group(1) == 'https' else 'http'}://{m.group(2)}"
    return None


def set_beds(item: Feature, row: dict) -> bool:
    if (beds := row.get("合計病床数")) and beds.isdigit() and int(beds) > 0:
        item["extras"]["beds"] = str(int(beds))
        return True
    return False


def parse_pharmacy_hours(row: dict) -> OpeningHours | None:
    oh = OpeningHours()
    for day_ja, day in DAY_PREFIXES:
        # 0 means closed and 1 means open for all of these fields.
        if row[f"営業日（{day_ja}）"] != "1" or row[f"定期閉店毎週（{day_ja}）"] == "0":
            oh.set_closed(day)
            continue
        if all(row[f"定期閉店第{chr(ord('０') + n)}週（{day_ja}）"] == "0" for n in range(1, 6)):
            oh.set_closed(day)
            continue
        if not add_ranges(oh, row, day, day_ja):
            return None
    # A facility with no open day is a data error.
    return oh if oh.day_hours else None


def add_ranges(oh: OpeningHours, row: dict, day: str, day_ja: str) -> bool:
    ranges = []
    for n in range(1, 5):
        start = row[f"{day_ja}_開店時間帯{n}_開始時間"]
        end = row[f"{day_ja}_開店時間帯{n}_終了時間"]
        if not (start and end):
            continue
        # Join back to back ranges such as 08:30-12:30 and 12:30-17:30.
        if ranges and ranges[-1][1] == start:
            ranges[-1][1] = end
        else:
            ranges.append([start, end])
    for start, end in ranges:
        oh.add_range(day, start, end)
    return bool(ranges)


def set_departments(item: Feature, row: dict, departments: tuple | None, specialities: dict[str, str]) -> None:
    if not departments:
        return
    codes, hours = departments
    values = []
    for code in codes:
        for value in specialities.get(code, "").split(";"):
            if value and value not in values:
                values.append(value)
    if values:
        item["extras"]["healthcare:speciality"] = ";".join(values)
    item["opening_hours"] = parse_department_hours(row, hours)


def parse_department_hours(row: dict, hours: list[set]) -> OpeningHours | None:
    oh = OpeningHours()
    for (day_ja, day), day_hours in zip(DAY_PREFIXES, hours):
        # 0 means closed and 1 means open for all of these fields.
        flag = row[f"毎週決まった曜日に休診（{day_ja}）"]
        if flag == "0" or not day_hours:
            if flag == "1":
                return None  # open on this day, but at unknown times
            oh.set_closed(day)
            continue
        if all(row[f"決まった週に休診（定期週）第{n}週（{day_ja}）"] == "0" for n in range(1, 6)):
            oh.set_closed(day)
            continue
        for start, end in merge_ranges(day_hours):
            oh.add_range(day, start, end)
    return oh if oh.day_hours else None


def merge_ranges(ranges: set[tuple[str, str]]) -> list[list[str]]:
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
