import json

from scrapy import Request, Spider

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

TAXONOMY_SPECIALITY_MAP = {
    "103T00000X": None,  # Clinical Psychology
    "1041C0700X": None,  # Clinical Social Worker
    "111N00000X": HealthcareSpecialities.CHIROPRATIC,
    "133N00000X": None,  # Nutritionist
    "133V00000X": None,  # Registered Dietitian
    "152W00000X": None,  # Optometry
    "163WP0807X": None,  # Pediatric Mental Health
    "163WW0000X": None,  # Wound Care
    "170300000X": None,  # Genetic Counselor
    "171100000X": HealthcareSpecialities.ACUPUNCTURE,
    "174H00000X": None,  # Diabetes Education
    "174MM1900X": None,  # Research
    "175F00000X": HealthcareSpecialities.NATUROPATHY,
    "204E00000X": HealthcareSpecialities.MAXILLOFACIAL,
    "207K00000X": HealthcareSpecialities.ALLERGOLOGY,
    "207L00000X": HealthcareSpecialities.ANAESTHETICS,
    "207N00000X": HealthcareSpecialities.DERMATOLOGY,
    "207P00000X": HealthcareSpecialities.EMERGENCY,
    "207PP0204X": None,  # Pediatric Emergency Medicine
    "207Q00000X": HealthcareSpecialities.GENERAL,
    "207R00000X": HealthcareSpecialities.INTERNAL,
    "207RC0000X": HealthcareSpecialities.CARDIOLOGY,
    "207RE0101X": HealthcareSpecialities.ENDOCRINOLOGY,
    "207RG0100X": HealthcareSpecialities.GASTROENTEROLOGY,
    "207RG0300X": HealthcareSpecialities.GERIATRICS,
    "207RH0000X": HealthcareSpecialities.HAEMATOLOGY,
    "207RH0002X": HealthcareSpecialities.PALLIATIVE,
    "207RI0008X": HealthcareSpecialities.HEPATOLOGY,
    "207RI0200X": HealthcareSpecialities.INFECTIOUS_DISEASES,
    "207RN0300X": HealthcareSpecialities.NEPHROLOGY,
    "207RP1001X": HealthcareSpecialities.PULMONOLOGY,
    "207RR0500X": HealthcareSpecialities.RHEUMATOLOGY,
    "207RS0012X": HealthcareSpecialities.SLEEP_MEDICINE,
    "207RX0202X": HealthcareSpecialities.ONCOLOGY,
    "207SG0201X": None,  # Medical Genetics
    "207U00000X": HealthcareSpecialities.NUCLEAR,
    "207V00000X": HealthcareSpecialities.GYNAECOLOGY,
    "207VB0002X": None,  # Bariatric (Weight Loss) Medicine
    "207VE0102X": None,  # Reproductive Endocrinology & Infertility
    "207W00000X": HealthcareSpecialities.OPHTHALMOLOGY,
    "207X00000X": HealthcareSpecialities.ORTHOPAEDICS,  # Orthopaedic Surgery
    "207XP3100X": None,  # Pediatric Orthopedics
    "207XS0117X": HealthcareSpecialities.ORTHOPAEDICS,  # Orthopaedic Surgery of the Spine
    "207XX0005X": HealthcareSpecialities.PHYSIATRY,  # Sports Medicine
    "207Y00000X": HealthcareSpecialities.OTOLARYNGOLOGY,
    "207ZP0102X": HealthcareSpecialities.PATHOLOGY,
    "208000000X": HealthcareSpecialities.PAEDIATRICS,
    "2080N0001X": HealthcareSpecialities.NEONATOLOGY,
    "2080P0202X": None,  # Pediatric Cardiology
    "2080P0205X": None,  # Pediatric Endocrinology
    "2080P0206X": None,  # Pediatric Gastroenterology
    "2080P0207X": None,  # Pediatric Hematology & Oncology
    "2080P0208X": None,  # Pediatric Infectious Disease
    "2080P0210X": None,  # Pediatric Nephrology
    "2080P0214X": None,  # Pediatric Pulmonology
    "2080P0216X": None,  # Pediatric Rheumatology
    "208100000X": HealthcareSpecialities.PHYSIATRY,  # Physical Medicine & Rehabilitation
    "2083P0901X": None,  # Preventive Medicine
    "2084N0400X": HealthcareSpecialities.NEUROLOGY,
    "2084N0402X": None,  # Child Neurology
    "2084P0800X": HealthcareSpecialities.PSYCHIATRY,
    "2084P0804X": HealthcareSpecialities.CHILD_PSYCHIATRY,
    "2085R0001X": None,  # Radiation Oncology
    "2085R0202X": HealthcareSpecialities.RADIOLOGY,
    "208600000X": HealthcareSpecialities.SURGERY,
    "2086S0122X": HealthcareSpecialities.PLASTIC_SURGERY,
    "2086S0129X": HealthcareSpecialities.VASCULAR_SURGERY,
    "208800000X": HealthcareSpecialities.UROLOGY,
    "208C00000X": HealthcareSpecialities.PROCTOLOGY,
    "208G00000X": HealthcareSpecialities.CARDIOTHORACIC_SURGERY,
    "208VP0000X": HealthcareSpecialities.PAIN_MEDICINE,
    "213E00000X": HealthcareSpecialities.PODIATRY,
    "225100000X": None,  # Physical Therapy
    "225X00000X": HealthcareSpecialities.OCCUPATIONAL,
    "231H00000X": None,  # Audiology
    "261QU0200X": None,  # Urgent Care
    "291U00000X": None,  # High-complexity Lab Testing
    "390200000X": None,  # Resident Physician
}


class CarbonHealthUSSpider(Spider):
    name = "carbon_health_us"
    item_attributes = {"brand": "Carbon Health", "brand_wikidata": "Q110076263"}

    def start_requests(self):
        yield Request("https://carbonhealth.com/locations", headers={"RSC": "1"})

    def parse(self, response):
        data = None
        for line in response.body.splitlines():
            line = line[line.find(b":") + 1 :].strip()
            if line[0] != ord("["):
                continue
            components = json.loads(line)
            for component in components:
                if isinstance(component, dict) and "locations" in component:
                    data = component
                    break
            if data is not None:
                break
        if data is None:
            raise Exception("Can't find data")

        specialty_id_to_speciality = {}
        urgent_care_specialty_ids = set()
        for specialty in data["allSpecialties"]:
            code = specialty["taxonomyCode"]
            if code in TAXONOMY_SPECIALITY_MAP:
                specialty_id_to_speciality[specialty["id"]] = TAXONOMY_SPECIALITY_MAP[code]
            else:
                self.crawler.stats.inc_value(f"atp/carbon_health/unmapped_specialty/{code}")
            if code == "261QU0200X":
                urgent_care_specialty_ids.add(specialty["id"])

        for location in data["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item["name"]
            item["name"] = self.item_attributes["brand"]

            item["image"] = f"https://images.carbonhealth.com/{location['coverImageId']}/2x.jpg"
            item["extras"]["ref:google"] = location["googlePlaceId"]
            item["website"] = f"https://carbonhealth.com/locations/{location['slug']}"

            address = location["address"]
            item["street_address"] = merge_address_lines([address["firstLine"], address["secondLine"]])
            item["extras"]["addr:unit"] = address["aptNumber"]
            item["lat"] = address["latitude"]
            item["lon"] = address["longitude"]

            oh = OpeningHours()
            for day in location["hours"]:
                oh.add_range(DAYS[(day["day"] - 1) % 7], day["from"], day["to"])
            item["opening_hours"] = oh

            apply_healthcare_specialities(
                filter(None, (specialty_id_to_speciality[specialty_id] for specialty_id in location["specialtyIds"])),
                item,
            )

            if any(specialty_id in urgent_care_specialty_ids for specialty_id in location["specialtyIds"]):
                apply_category(Categories.CLINIC_URGENT, item)

            if any(service["name"] == "Vaccination Administration" for service in location["services"]):
                apply_healthcare_specialities([HealthcareSpecialities.VACCINATION], item)

            yield item
