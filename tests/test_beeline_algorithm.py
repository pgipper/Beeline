# -*- coding: utf-8 -*-
import pytest

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsVectorLayer,
)
from qgis import processing


# ---------------------------------------------------------------------------
# Helper to build a memory point layer
# ---------------------------------------------------------------------------

def _make_point_layer(points: list[tuple[float, float]], epsg: int = 4326) -> QgsVectorLayer:
    """Create a memory point layer from a list of (x, y) tuples."""
    crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
    layer = QgsVectorLayer(f"Point?crs=EPSG:{epsg}", "points", "memory")
    assert layer.isValid(), f"Could not create memory layer for EPSG:{epsg}"
    provider = layer.dataProvider()
    features = []
    for x, y in points:
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        features.append(feat)
    provider.addFeatures(features)
    layer.updateExtents()
    return layer


# ---------------------------------------------------------------------------
# 1. Algorithm registration & metadata
# ---------------------------------------------------------------------------

class TestAlgorithmRegistration:

    def test_provider_registered(self, beeline_provider):
        assert beeline_provider.id() == "beelines"
        assert beeline_provider.name() == "Beelines"

    def test_algorithm_exists(self, beeline_provider):
        alg = beeline_provider.algorithm("beelines")
        assert alg is not None

    def test_algorithm_metadata(self, beeline_provider):
        alg = beeline_provider.algorithm("beelines")
        assert alg.name() == "beelines"
        assert alg.displayName() == "Beelines"
        assert alg.shortHelpString()

    def test_algorithm_has_create_instance(self, beeline_provider):
        alg = beeline_provider.algorithm("beelines")
        instance = alg.createInstance()
        assert instance is not None
        assert instance.name() == "beelines"


# ---------------------------------------------------------------------------
# 2. Basic beeline generation (EPSG:4326)
# ---------------------------------------------------------------------------

class TestBasicBeelines:

    def test_three_points_produce_three_lines(self, beeline_provider, qgis_new_project):
        """3 points → C(3,2) = 3 beelines."""
        layer = _make_point_layer([(0, 0), (10, 10), (20, 20)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert isinstance(out, QgsVectorLayer)
        assert out.featureCount() == 3

    def test_two_points_produce_one_line(self, beeline_provider, qgis_new_project):
        layer = _make_point_layer([(0, 0), (45, 45)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        assert result["OUTPUT"].featureCount() == 1

    def test_output_has_expected_fields(self, beeline_provider, qgis_new_project):
        layer = _make_point_layer([(0, 0), (10, 10)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        field_names = [f.name() for f in out.fields()]
        assert "source_id" in field_names
        assert "target_id" in field_names
        assert "distance" in field_names

    def test_output_geometry_is_multilinestring(self, beeline_provider, qgis_new_project):
        layer = _make_point_layer([(0, 0), (10, 10)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        feat = next(result["OUTPUT"].getFeatures())
        assert feat.geometry().isMultipart()
        assert "LineString" in feat.geometry().asWkt()


# ---------------------------------------------------------------------------
# 3. Different CRS inputs
# ---------------------------------------------------------------------------

class TestDifferentCRS:

    def test_epsg_32632_utm(self, beeline_provider, qgis_new_project):
        """UTM Zone 32N – projected CRS."""
        # ~Berlin and ~Munich in EPSG:32632
        layer = _make_point_layer([(389279, 5819966), (691852, 5334747)], epsg=32632)
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert out.featureCount() == 1
        feat = next(out.getFeatures())
        assert feat["distance"] > 0

    def test_epsg_3857_web_mercator(self, beeline_provider, qgis_new_project):
        """Web Mercator."""
        # London and Paris in EPSG:3857
        layer = _make_point_layer([(-14138, 6711544), (261634, 6250566)], epsg=3857)
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert out.featureCount() == 1
        feat = next(out.getFeatures())
        assert feat["distance"] > 0

    def test_geographic_crs_epsg_4269_nad83(self, beeline_provider, qgis_new_project):
        """NAD83 geographic CRS."""
        # New York and Los Angeles
        layer = _make_point_layer([(-74.006, 40.7128), (-118.2437, 34.0522)], epsg=4269)
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert out.featureCount() == 1
        feat = next(out.getFeatures())
        # ~3,940 km
        assert 3_500_000 < feat["distance"] < 4_500_000


# ---------------------------------------------------------------------------
# 4. Segment size parameter
# ---------------------------------------------------------------------------

class TestSegmentSize:

    def test_smaller_segment_produces_more_vertices(self, beeline_provider, qgis_new_project):
        """Smaller segment size → denser polyline."""
        layer = _make_point_layer([(0, 0), (30, 30)])

        result_large = processing.run(
            "beelines:beelines",
            {
                "INPUT": layer,
                "SEGMENT_SIZE": 500_000,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )
        result_small = processing.run(
            "beelines:beelines",
            {
                "INPUT": layer,
                "SEGMENT_SIZE": 50_000,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )

        def _vertex_count(lyr):
            feat = next(lyr.getFeatures())
            geom = feat.geometry()
            return sum(len(part) for part in geom.asMultiPolyline())

        verts_large = _vertex_count(result_large["OUTPUT"])
        verts_small = _vertex_count(result_small["OUTPUT"])
        assert verts_small > verts_large, (
            f"Expected more vertices with small segments ({verts_small}) "
            f"than large ({verts_large})"
        )

    def test_distance_independent_of_segment_size(self, beeline_provider, qgis_new_project):
        """Distance attribute must not change with segment size."""
        layer = _make_point_layer([(0, 0), (30, 30)])

        r1 = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "SEGMENT_SIZE": 100_000, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        r2 = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "SEGMENT_SIZE": 500_000, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )

        d1 = next(r1["OUTPUT"].getFeatures())["distance"]
        d2 = next(r2["OUTPUT"].getFeatures())["distance"]
        assert pytest.approx(d1, rel=1e-6) == d2


# ---------------------------------------------------------------------------
# 5. Antimeridian split
# ---------------------------------------------------------------------------

class TestAntimeridianSplit:

    def _run_antimeridian(self, beeline_provider, split: bool):
        """Helper: run beeline across the antimeridian."""
        # Tokyo → Los Angeles crosses the antimeridian
        layer = _make_point_layer([(139.6917, 35.6895), (-118.2437, 34.0522)])
        return processing.run(
            "beelines:beelines",
            {
                "INPUT": layer,
                "ANTIMERIDIAN_SPLIT": split,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )

    def test_split_on_produces_multipart(self, beeline_provider, qgis_new_project):
        """With antimeridian split enabled, the geometry should have >1 parts."""
        result = self._run_antimeridian(beeline_provider, split=True)
        feat = next(result["OUTPUT"].getFeatures())
        parts = feat.geometry().asMultiPolyline()
        assert len(parts) > 1, "Expected multiple parts when splitting at antimeridian"

    def test_split_off_produces_single_part(self, beeline_provider, qgis_new_project):
        """With split disabled, the line should have exactly 1 part."""
        result = self._run_antimeridian(beeline_provider, split=False)
        feat = next(result["OUTPUT"].getFeatures())
        parts = feat.geometry().asMultiPolyline()
        assert len(parts) == 1, "Expected single part when not splitting at antimeridian"

    def test_distance_same_regardless_of_split(self, beeline_provider, qgis_new_project):
        """Distance must be identical whether we split or not."""
        r_on = self._run_antimeridian(beeline_provider, split=True)
        r_off = self._run_antimeridian(beeline_provider, split=False)
        d_on = next(r_on["OUTPUT"].getFeatures())["distance"]
        d_off = next(r_off["OUTPUT"].getFeatures())["distance"]
        assert pytest.approx(d_on, rel=1e-6) == d_off


# ---------------------------------------------------------------------------
# 6. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_single_point_no_output(self, beeline_provider, qgis_new_project):
        """A single point produces zero beelines."""
        layer = _make_point_layer([(0, 0)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        assert result["OUTPUT"].featureCount() == 0

    def test_coincident_points(self, beeline_provider, qgis_new_project):
        """Two identical points → one beeline with distance ≈ 0."""
        layer = _make_point_layer([(10, 50), (10, 50)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert out.featureCount() == 1
        feat = next(out.getFeatures())
        assert feat["distance"] == pytest.approx(0, abs=1)

    def test_four_points(self, beeline_provider, qgis_new_project):
        """4 points → C(4,2) = 6 beelines."""
        layer = _make_point_layer([(0, 0), (10, 0), (10, 10), (0, 10)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        assert result["OUTPUT"].featureCount() == 6

    def test_antipodal_points(self, beeline_provider, qgis_new_project):
        """Near-antipodal points should still produce a valid result."""
        layer = _make_point_layer([(0, 89), (180, -89)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        out = result["OUTPUT"]
        assert out.featureCount() == 1
        feat = next(out.getFeatures())
        assert feat["distance"] > 0
        assert not feat.geometry().isEmpty()


# ---------------------------------------------------------------------------
# 7. Distance plausibility
# ---------------------------------------------------------------------------

class TestDistanceValues:

    def test_distance_berlin_to_munich(self, beeline_provider, qgis_new_project):
        """Berlin–Munich ≈ 504 km geodesic."""
        layer = _make_point_layer([(13.405, 52.52), (11.582, 48.1351)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        dist = next(result["OUTPUT"].getFeatures())["distance"]
        # Allow 2 % tolerance
        assert 490_000 < dist < 520_000, f"Expected ~504 km, got {dist / 1000:.1f} km"

    def test_distance_london_to_new_york(self, beeline_provider, qgis_new_project):
        """London–New York ≈ 5,570 km geodesic."""
        layer = _make_point_layer([(-0.1276, 51.5074), (-74.006, 40.7128)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        dist = next(result["OUTPUT"].getFeatures())["distance"]
        assert 5_400_000 < dist < 5_700_000, f"Expected ~5570 km, got {dist / 1000:.1f} km"

    def test_distance_equator_one_degree(self, beeline_provider, qgis_new_project):
        """1° along the equator ≈ 111.32 km."""
        layer = _make_point_layer([(0, 0), (1, 0)])
        result = processing.run(
            "beelines:beelines",
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
        )
        dist = next(result["OUTPUT"].getFeatures())["distance"]
        assert 110_000 < dist < 113_000, f"Expected ~111.3 km, got {dist / 1000:.1f} km"
