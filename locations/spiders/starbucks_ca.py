from locations.spiders.starbucks_us import StarbucksUSSpider


class StarbucksCASpider(StarbucksUSSpider):
    name = "starbucks_ca"
    item_attributes = StarbucksUSSpider.item_attributes
    searchable_point_files = ["ca_centroids_50mile_radius.csv"]
    country_filter = ["CA"]
