from locations.storefinders.locally import LocallySpider


class AsicsUSSpider(LocallySpider):
    name = "asics_us"
    item_attributes = {"brand": "ASICS", "brand_wikidata": "Q327247"}
    start_urls = [
        "https://www.locally.com/stores/conversion_data?has_data=true&company_id=1682&map_distance_diag=25000"
    ]

    def post_process_item(self, item, response, location):
        if location["company_id"] == 1682:
            item["street_address"] = item.pop("addr_full")
            if item["name"].startswith("ASICS Outlet "):
                item["branch"] = item["name"].removeprefix("ASICS Outlet ")
                item["name"] = "ASICS Outlet"
            else:
                item["branch"] = item["name"].removeprefix("ASICS ")
                item["name"] = "ASICS"
            yield item
