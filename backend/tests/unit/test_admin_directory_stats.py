from app.services.admin_directory_stats import compute_growth_percent


def test_compute_growth_percent_increase():
    assert compute_growth_percent(15, 10) == 50.0


def test_compute_growth_percent_decrease():
    assert compute_growth_percent(5, 10) == -50.0


def test_compute_growth_percent_from_zero():
    assert compute_growth_percent(10, 0) == 100.0
    assert compute_growth_percent(0, 0) == 0.0
