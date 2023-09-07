import os


def open_searchable_points(filename):
    return open(get_searchable_points_path(filename))


def get_searchable_points_path(filename):
    return f"{os.path.dirname(os.path.realpath(__file__))}/{filename}"
