from locations.spiders.subway import SubwaySpider
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SubwaySGSpider(AgileStoreLocatorSpider):
    name = "subway_sg"
    item_attributes = SubwaySpider.item_attributes
    allowed_domains = ["subwayisfresh.com.sg"]
