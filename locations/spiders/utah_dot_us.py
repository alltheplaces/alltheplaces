from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class UtahDotUSSpider(NevadaDotUSSpider):
    name = "utah_dot_us"
    item_attributes = {"operator": "Utah DOT", "operator_wikidata": "Q2506783"}
    start_urls = ["https://prod-ut.ibi511.com/map/mapIcons/Cameras"]
