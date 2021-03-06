import json
from typing import Any, Optional
from unittest import TestCase
from unittest.mock import patch

import ujson
from pytest import approx, raises

from zoloto.calibration import CalibrationParameters
from zoloto.cameras.marker import MarkerCamera as BaseMarkerCamera
from zoloto.exceptions import MissingCalibrationsError
from zoloto.marker import Marker
from zoloto.marker_type import MarkerType


class MarkerTestCase(TestCase):
    MARKER_SIZE = 200
    MARKER_ID = 25

    def setUp(self) -> None:
        class MarkerCamera(BaseMarkerCamera):
            marker_type = MarkerType.DICT_6X6_50

        self.marker_camera = MarkerCamera(
            self.MARKER_ID, marker_size=self.MARKER_SIZE
        )  # type: BaseMarkerCamera
        self.markers = list(self.marker_camera.process_frame())
        self.marker = self.markers[0]

    def test_marker_size(self) -> None:
        self.assertEqual(self.marker.size, self.MARKER_SIZE)

    def test_marker_id(self) -> None:
        self.assertEqual(self.marker.id, self.MARKER_ID)

    def test_pixel_corners(self) -> None:
        self.assertEqual(len(self.marker.pixel_corners), 4)
        border_size = self.marker_camera.BORDER_SIZE
        tl, tr, br, bl = self.marker.pixel_corners
        self.assertEqual(tl, (border_size, border_size))
        self.assertEqual(tr, (self.MARKER_SIZE + border_size - 1, border_size))
        self.assertEqual(
            br,
            (self.MARKER_SIZE + border_size - 1, self.MARKER_SIZE + border_size - 1),
        )
        self.assertEqual(bl, (border_size, self.MARKER_SIZE + border_size - 1))

    def test_pixel_centre(self) -> None:
        tl, _, br, _ = self.marker.pixel_corners
        self.assertEqual(self.marker.pixel_centre, (139, 139))

    def test_distance(self) -> None:
        self.assertEqual(self.marker.distance, 992)

    def test_orientation(self) -> None:
        rot_x, rot_y, rot_z = self.marker.orientation
        self.assertEqual(int(rot_x), -3)
        self.assertEqual(int(rot_y), 0)
        self.assertEqual(int(rot_z), 0)

    def test_cartesian_coordinates(self) -> None:
        x, y, z = self.marker.cartesian
        self.assertEqual(int(x), 49)
        self.assertEqual(int(y), 24)
        self.assertEqual(int(z), 991)

    def test_spherical_coordinates(self) -> None:
        rot_x, rot_y, dist = self.marker.spherical
        self.assertEqual(dist, self.marker.distance)
        self.assertEqual(rot_x, approx(0.025, abs=1e-3))
        self.assertEqual(rot_y, approx(0.05, abs=1e-3))

    def test_as_dict(self) -> None:
        marker_dict = self.marker.as_dict()
        self.assertIsInstance(marker_dict, dict)
        self.assertEqual(
            {"id", "size", "pixel_corners", "rvec", "tvec"}, set(marker_dict.keys())
        )
        self.assertEqual(marker_dict["size"], self.MARKER_SIZE)
        self.assertEqual(marker_dict["id"], self.MARKER_ID)

    def test_dict_as_json(self) -> None:
        marker_dict = self.marker.as_dict()
        created_marker_dict = json.loads(json.dumps(marker_dict))
        self.assertEqual(marker_dict, created_marker_dict)

    def test_many_as_ujson(self) -> None:
        created_markers_dict = ujson.loads(
            ujson.dumps([m.as_dict() for m in self.markers])
        )
        self.assertEqual(len(created_markers_dict), 1)
        self.assertEqual(
            {marker["id"] for marker in created_markers_dict}, {self.MARKER_ID}
        )

    def test_dict_as_ujson(self) -> None:
        marker_dict = self.marker.as_dict()
        created_marker_dict = ujson.loads(ujson.dumps(marker_dict))
        self.assertEqual(marker_dict["id"], created_marker_dict["id"])
        self.assertEqual(marker_dict["size"], created_marker_dict["size"])
        for expected_corner, corner in zip(
            marker_dict["pixel_corners"], created_marker_dict["pixel_corners"]
        ):
            self.assertEqual(expected_corner, approx(corner))
        self.assertEqual(marker_dict["rvec"], approx(created_marker_dict["rvec"]))
        self.assertEqual(marker_dict["tvec"], approx(created_marker_dict["tvec"]))


class EagerMarkerTestCase(MarkerTestCase):
    def setUp(self) -> None:
        class MarkerCamera(BaseMarkerCamera):
            marker_type = MarkerType.DICT_6X6_50

        self.marker_camera = MarkerCamera(self.MARKER_ID, marker_size=self.MARKER_SIZE)
        self.markers = list(self.marker_camera.process_frame_eager())
        self.marker = self.markers[0]

    def test_is_eager(self) -> None:
        self.assertTrue(self.marker._is_eager())

    @patch("cv2.aruco.estimatePoseSingleMarkers")
    def test_doesnt_calculate_pose(self, pose_mock: Any) -> None:
        assert self.marker._tvec is not None
        assert self.marker._rvec is not None
        pose_mock.assert_not_called()


class MarkerFromDictTestCase(EagerMarkerTestCase):
    def setUp(self) -> None:
        class MarkerCamera(BaseMarkerCamera):
            marker_type = MarkerType.DICT_6X6_50

        self.marker_camera = MarkerCamera(self.MARKER_ID, marker_size=self.MARKER_SIZE)
        self.markers = list(self.marker_camera.process_frame())
        self.marker = Marker.from_dict(self.markers[0].as_dict())


class MarkerSansCalibrationsTestCase(MarkerTestCase):
    class TestCamera(BaseMarkerCamera):
        marker_type = MarkerType.DICT_6X6_50

        def get_calibrations(self) -> Optional[CalibrationParameters]:
            return None

    def setUp(self) -> None:
        self.marker_camera = self.TestCamera(
            self.MARKER_ID, marker_size=self.MARKER_SIZE,
        )
        self.markers = list(self.marker_camera.process_frame())
        self.marker = self.markers[0]

    def __getattribute__(self, name: str) -> Any:
        attr = super().__getattribute__(name)
        if name in [
            "test_orientation",
            "test_distance",
            "test_cartesian_coordinates",
            "test_spherical_coordinates",
        ]:

            def test_raises(*args: Any, **kwargs: Any) -> None:
                with raises(MissingCalibrationsError):
                    attr(*args, **kwargs)

            return test_raises
        return attr

    def test_as_dict(self) -> None:
        marker_dict = self.marker.as_dict()
        self.assertIsInstance(marker_dict, dict)
        self.assertEqual({"id", "size", "pixel_corners"}, set(marker_dict.keys()))
        self.assertEqual(marker_dict["size"], self.MARKER_SIZE)
        self.assertEqual(marker_dict["id"], self.MARKER_ID)

    def test_dict_as_ujson(self) -> None:
        marker_dict = self.marker.as_dict()
        created_marker_dict = ujson.loads(ujson.dumps(marker_dict))
        self.assertEqual(marker_dict["id"], created_marker_dict["id"])
        self.assertEqual(marker_dict["size"], created_marker_dict["size"])
        for expected_corner, corner in zip(
            marker_dict["pixel_corners"], created_marker_dict["pixel_corners"]
        ):
            self.assertEqual(expected_corner, approx(corner))
        self.assertNotIn("rvec", created_marker_dict)
        self.assertNotIn("tvec", created_marker_dict)


class MarkerSansCalibrationsFromDictTestCase(MarkerSansCalibrationsTestCase):
    def setUp(self) -> None:
        self.marker_camera = self.TestCamera(
            self.MARKER_ID, marker_size=self.MARKER_SIZE,
        )
        self.markers = list(self.marker_camera.process_frame())
        self.marker = Marker.from_dict(self.markers[0].as_dict())

    def test_is_not_eager(self) -> None:
        self.assertFalse(self.marker._is_eager())
