from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class RunzaUSSpider(JSONBlobSpider):
    name = "runza_us"
    start_urls = [
        "https://drupal.runza.com/api/locations?proximity[value]=15&proximity[source_configuration][origin][lat]=&proximity[source_configuration][origin][lon]="
    ]

    def post_process_item(self, item, response, location):
        item["lat"] = location["field_lat_lon"][0]["lat"]
        item["lon"] = location["field_lat_lon"][0]["lon"]
        item["street_address"] = merge_address_lines(
            [location["field_address"][0]["address_line1"], location["field_address"][0]["address_line2"]]
        )
        item["city"] = location["field_address"][0]["locality"]
        item["state"] = location["field_address"][0]["administrative_area"]
        item["postcode"] = location["field_address"][0]["postal_code"]
        item["ref"] = location["uuid"][0]["value"]
        item.pop("name", None)

        if location["field_hide_dining_room_hours"][0]["value"] is False:
            oh = OpeningHours()
            for day in range(0, 7):
                day_hours = location["field_dining_room_hours"][day]
                if day_hours:
                    oh.add_range(
                        day=DAYS[day],
                        open_time=f"{day_hours['starthours']}",
                        close_time=f"{day_hours['endhours']}",
                        time_format="%H%M",
                    )
            item["opening_hours"] = oh

        if location["field_hide_drive_thru_hours"][0]["value"] is False:
            oh = OpeningHours()
            for day in range(0, 7):
                day_hours = location["field_drive_thru_hours"][day]
                if day_hours:
                    oh.add_range(
                        day=DAYS[day],
                        open_time=f"{day_hours['starthours']}",
                        close_time=f"{day_hours['endhours']}",
                        time_format="%H%M",
                    )
            item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()

        yield item
