import pytest

from qgis.core import QgsApplication

from beeline_algorithm import BeelineProvider


@pytest.fixture(scope="session")
def beeline_provider(qgis_processing):
    """Register the BeelineProvider so 'beelines:beelines' is available."""
    provider = BeelineProvider()
    QgsApplication.processingRegistry().addProvider(provider)
    yield provider
    QgsApplication.processingRegistry().removeProvider(provider)
