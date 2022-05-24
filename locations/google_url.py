from urllib.parse import parse_qsl


def url_to_coords(url: str) -> (float, float):
    if url.startswith("https://www.google.com/maps/embed?pb="):
        # https://andrewwhitby.com/2014/09/09/google-maps-new-embed-format/
        params = url[38:].split("!")

        for i in range(0, len(params)):
            if params[i] == "1m3":
                lat = 0
                lon = 0

                for k in range(i + 1, i + 4):
                    if params[k][:2] == "2d":
                        lon = float(params[k][2:])
                    elif params[k][:2] == "3d":
                        lat = float(params[k][2:])

                return lat, lon
    elif url.startswith("https://maps.googleapis.com/maps/api/staticmap"):
        query = dict(parse_qsl(url))
        lat, lon = query["center"].split(",")
        return float(lat), float(lon)

    return None
