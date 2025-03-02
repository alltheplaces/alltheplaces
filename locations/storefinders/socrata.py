# Documentation: https://dev.socrata.com/

# Get columns (schema) from https://data.cityofnewyork.us/api/views/hn5i-inap.json?read_from_nbe=true&version=2.1

# Check last modification date is within last year or so (see ArcGISSpider for example)

# Get feature count from https://data.cityofnewyork.us/resource/hn5i-inap.json?$query=SELECT%20count(%27*%27)%20as%20__count_alias__

# Request pages of results using https://data.cityofnewyork.us/resource/hn5i-inap.geojson?$limit=50000&$offset=200000 (or whatever offsets calculated from total feature count)

# Examples: NYC Parks, ACT Government (ACT road safety cameras spider needs converting), etc.
# Search for "Content built off this asset will live here." on Google to find more.

from datetime import UTC, datetime, timedelta
from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class SocrataSpider(Spider):
    """
    Official documentation of the Socrata Open Data API:
    https://dev.socrata.com/

    To use this store finder, specify a `host` and `resource_id`. Optionally
    specify `page_size` if the server has been configured to return a smaller
    number of records at a time than the default of 50000. Optionally specify
    `field_names` if it is beneficial to only work with a subset of all fields
    available within the dataset. These attributes can be extracted from URLs
    as follows:
      https://{host}/{resource_id}.json?$limit={page_size}&$select={field_names_serialized}
      (where {field_name_serialized} is ",".join(field_names))

    Each feature within the specified dataset is run through `DictParser.parse`
    to try and automatically extract as much information as possible. Override
    the `pre_process_data` function to modify field values before
    `DictParser.parse` is called. Override the `post_process_item` function to
    extract additional information from the source feature or to clean data
    after automatic extraction has been attempted.

    Warnings will raised if any of the following conditions occur:
      1. Source data has a last data modification timestamp greater than 365
         days ago. This warning is a prompt to double check the latest source
         data is in use and that the brand/operator hasn't changed systems for
         publishing geographic information about features.
      2. A field defined in the `field_names` attribute is not present in the
         requested layer. This may indicate the data publisher has changed the
         schema of the feature layer to omit, rename or replace a field.

    The Socrata Open Data API has throttling included for the public and HTTP
    429 responses may be received. In such an event, set `DOWNLOAD_DELAY` to a
    higher value.
    """

    dataset_attributes = {"source": "api", "api": "socrata"}

    host: str = ""
    resource_id: str = ""
    page_size: int = 50000
    field_names: list[str] = []

    # Pages of results can be quite large and may take a while to export and
    # download. The download size warning is increased to 256MiB.
    custom_settings = {"DOWNLOAD_TIMEOUT": 120, "DOWNLOAD_WARNSIZE": 268435456}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=f"https://{self.host}/resource/{self.resource_id}.json?$query=SELECT count(*) AS total_records", callback=self.parse_record_count)

    def parse_record_count(self, response: Response) -> Iterable[JsonRequest]:
        total_records = int(response.json()[0]["total_records"])
        yield JsonRequest(url=f"https://{self.host}/api/views/{self.resource_id}.json", meta={"total_records": total_records}, callback=self.parse_schema)

    def parse_schema(self, response: Response) -> Iterable[JsonRequest]:
        table_attributes = response.json()

        timestamp_of_last_edit = datetime.fromtimestamp(table_attributes["rowsUpdatedAt"], UTC)
        self.dataset_attributes.update({"source:date": timestamp_of_last_edit.isoformat()})
        current_timestamp = datetime.now(UTC)
        if current_timestamp - timestamp_of_last_edit > timedelta(days=365):
            self.logger.warning("The requested dataset is possibly outdated as the dataset was last edited over 365 days ago on {}.".format(timestamp_of_last_edit.isoformat()))

        select_clause = "&$select=*"
        if len(self.field_names) > 1:
            available_field_names = [column["fieldName"] for column in table_attributes["columns"]]
            output_field_names = []
            for field_name in self.field_names:
                if field_name not in available_field_names:
                    self.logger.warning("Spider requested that field `{}` be extracted for each feature in the dataset but the dataset doesn't have a field named `{}`. Field ignored.".format(field_name, field_name))
                    continue
                output_field_names.append(field_name)
            select_clause = "&$select=" + ",".join(output_field_name)

        for offset in range(0, response.meta["total_records"], self.page_size):
            yield JsonRequest(url=f"https://{self.host}/resource/{self.resource_id}.geojson?$limit={self.page_size}&$offset={offset}{select_clause}", callback=self.parse_features)

    def parse_features(self, response: Response) -> Iterable[Feature]:
        features = response.json()["features"]

        for feature in features:
            properties = feature.pop("properties")
            if "geometry" in properties.keys():
                # Prevent unlikely (but still possible) overwriting of feature
                # geometry if GeoJSON properties include a "geometry" field.
                properties["__geometry"] = properties.pop("geometry")
            feature.update(properties)
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature)

    def pre_process_data(self, feature: dict) -> None:
        return

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        yield item
