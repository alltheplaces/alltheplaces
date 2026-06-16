from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VictorianGovernmentSchoolsAUSpider(JSONBlobSpider):
    name = "victorian_government_schools_au"
    item_attributes = {"operator": "Victorian Department of Education", "operator_wikidata": "Q5260272"}
    allowed_domains = ["www.vic.gov.au"]
    start_urls = ["https://www.vic.gov.au/api/tide/elasticsearch/content-vic__production__sapi_node/_search"]
    locations_key = ["hits", "hits"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {
            "from": 0,
            "query": {
                "bool": {
                    "filter": [{"terms": {"type": ["det_150_content"]}}, {"terms": {"field_node_site": [4]}}],
                    "must": [{"match_all": {}}],
                }
            },
            "size": 10000,
            "sort": [{"_score": "desc"}, {"title.keyword": "asc"}],
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("_source"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        match feature["field_school_status_name"][0]:
            case "Open":
                pass
            case "Closed":
                return
            case _:
                self.logger.warning(
                    "Unknown school status '{}' for school '{}'.".format(
                        feature["field_school_status_name"][0], feature["field_school_number"][0]
                    )
                )

        item["ref"] = feature["field_school_number"][0]
        item["name"] = feature["title"][0].split(" - ", 1)[0]
        item["lat"] = float(feature["field_latitude_value"][0])
        item["lon"] = float(feature["field_longitude_value"][0])
        if feature.get("field_street_address"):
            item["street_address"] = feature["field_street_address"][0]
        if feature.get("field_suburb"):
            item["city"] = feature["field_suburb"][0]
        if feature.get("field_postcode"):
            item["postcode"] = feature["field_postcode"][0]
        if feature.get("field_email"):
            item["email"] = feature["field_email"][0]
        item.pop("website", None)

        self.extract_school_type(item, feature)

        if feature.get("field_open_date"):
            item["extras"]["start_date"] = feature["field_open_date"][0].split("T", 1)[0]

        yield item

    def extract_school_type(self, item: Feature, feature: dict) -> None:
        match feature["field_school_type_name"][0]:
            case "Primary":
                apply_category(Categories.SCHOOL, item)
                item["extras"]["school"] = "primary"
                item["extras"]["grades"] = "0-6"
                item["extras"]["isced:level:2011"] = "1"
            case "Primary and secondary":
                apply_category(Categories.SCHOOL, item)
                item["extras"]["school"] = "primary;secondary"
                if "P-9" in item["name"]:
                    item["extras"]["grades"] = "0-9"
                    item["extras"]["isced:level:2011"] = "1;2"
                else:
                    # Sometimes (but not always) containing P-12 in name
                    item["extras"]["grades"] = "0-12"
                    item["extras"]["isced:level:2011"] = "1;2;3"
            case "Secondary":
                apply_category(Categories.SCHOOL, item)
                item["extras"]["school"] = "secondary"
                if "Senior College" in item["name"]:
                    item["extras"]["grades"] = "10-12"
                    item["extras"]["isced:level:2011"] = "3"
                elif "Middle Years" in item["name"]:
                    item["extras"]["grades"] = "7-9"
                    item["extras"]["isced:level:2011"] = "2"
                else:
                    item["extras"]["grades"] = "7-12"
                    item["extras"]["isced:level:2011"] = "2;3"
            case "Special":
                apply_category(Categories.SCHOOL, item)
                item["extras"]["school"] = "special_education_needs"
            case "Language":
                apply_category(Categories.LANGUAGE_SCHOOL, item)
            case "Camp":
                apply_category(Categories.NATURE_SCHOOL, item)
            case _:
                self.logger.warning(
                    "Unknown school type '{}' for school '{}'.".format(
                        feature["field_school_type_name"][0], feature["field_school_number"][0]
                    )
                )
