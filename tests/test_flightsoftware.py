import pytest

from FlightSoftware import FlightSoftware


@pytest.fixture()
def fs():
    return FlightSoftware()


def test_get_total_propellant(fs):
    # telemetry values are in kg
    fs.telemetry['booster'] = {'fuelMass': 500000.0, 'oxidizerMass': 1500000.0}
    total = fs.get_total_propellant('booster')
    assert pytest.approx(total, rel=1e-6) == (500000.0 + 1500000.0) / 1000


def test_get_fuel_percent_booster(fs):
    fs.telemetry['booster'] = {'fuelMass': 739160.0}
    # max for booster in kg = 739.160 * 1000 = 739160.0
    assert pytest.approx(fs.get_fuel_percent('booster'), rel=1e-6) == 100.0


def test_get_lox_percent_ship(fs):
    fs.telemetry['ship'] = {'oxidizerMass': 1173851.0}
    # ship max lox kg = 1173.851 * 1000 = 1173851.0
    assert pytest.approx(fs.get_lox_percent('ship'), rel=1e-6) == 100.0
