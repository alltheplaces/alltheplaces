from locations.hours import DAYS_HU
from locations.spiders.lidl_at import LidlATSpider


class LidlHUSpider(LidlATSpider):
    name = "lidl_hu"

    dataset_id = "4c781cd459b444558df3d574f082358d"
    dataset_name = "Filialdaten-HU/Filialdaten-HU"
    api_key = "Ao1GqKj4R8CqJrqpewEs49enx3QSzeWBPtSei353drKi3WWHOzPad_qzp3Fn7qs0"
    days = DAYS_HU
