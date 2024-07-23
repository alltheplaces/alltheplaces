import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import shapely

from locations.hours import OpeningHours

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class HuqAdjustPipeline:
    """Minor tweaks to the 'default' AllThePlaces structure to simplify BigQuery import"""

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        self._process_extras(item)
        self._process_geometry(item)
        self._process_opening_hours(item)
        return item

    def _process_extras(self, item: Dict[str, Any]) -> None:
        extras = item.get("extras", {})
        for key in ["spider", "shop", "amenity"]:
            if key in extras:
                item[key] = extras[key]
        item["extras"] = [{"key": k, "value": v} for k, v in extras.items()]

    def _process_geometry(self, item: Dict[str, Any]) -> None:
        geometry = item.get("geometry", {})
        if geometry:
            item["geometry"] = shapely.to_wkt(shapely.from_geojson(json.dumps(geometry)))

    def _process_opening_hours(self, item: Dict[str, Any]) -> None:
        opening_hours = item.get("opening_hours", {})
        if isinstance(opening_hours, OpeningHours):
            item["opening_hours"] = opening_hours.as_opening_hours()
        # If it's already a string, we leave it as is
