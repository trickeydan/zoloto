from enum import IntEnum
from typing import Generator

from cv2 import aruco


class MarkerDict(IntEnum):
    DICT_4X4_50 = aruco.DICT_4X4_50
    DICT_4X4_100 = aruco.DICT_4X4_100
    DICT_4X4_250 = aruco.DICT_4X4_250
    DICT_4X4_1000 = aruco.DICT_4X4_1000
    DICT_5X5_50 = aruco.DICT_5X5_50
    DICT_5X5_100 = aruco.DICT_5X5_100
    DICT_5X5_250 = aruco.DICT_5X5_250
    DICT_5X5_1000 = aruco.DICT_5X5_1000
    DICT_6X6_50 = aruco.DICT_6X6_50
    DICT_6X6_100 = aruco.DICT_6X6_100
    DICT_6X6_250 = aruco.DICT_6X6_250
    DICT_6X6_1000 = aruco.DICT_6X6_1000
    DICT_7X7_50 = aruco.DICT_7X7_50
    DICT_7X7_100 = aruco.DICT_7X7_100
    DICT_7X7_250 = aruco.DICT_7X7_250
    DICT_7X7_1000 = aruco.DICT_7X7_1000
    DICT_ARUCO_ORIGINAL = aruco.DICT_ARUCO_ORIGINAL
    DICT_APRILTAG_16H5 = aruco.DICT_APRILTAG_16H5
    DICT_APRILTAG_25H9 = aruco.DICT_APRILTAG_25H9
    DICT_APRILTAG_36H10 = aruco.DICT_APRILTAG_36H10
    DICT_APRILTAG_36H11 = aruco.DICT_APRILTAG_36H11


def all_marker_dicts() -> Generator[MarkerDict, None, None]:
    yield from MarkerDict._member_map_.values()  # type: ignore
