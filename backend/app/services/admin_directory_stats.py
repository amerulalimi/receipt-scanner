from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.schemas.admin_directory import RegistrationStatPoint, RegistrationStatsData


def compute_growth_percent(current: int, previous: int) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def build_registration_stats(
    rows: list[tuple[datetime | str, int]],
    *,
    granularity: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> RegistrationStatsData:
    if not rows:
        return RegistrationStatsData(
            series=[],
            growth_percent=0.0,
            growth_label=_growth_label(granularity),
            total_in_range=0,
        )

    normalized_rows = [
        (_normalize_period(period, granularity), count) for period, count in rows
    ]
    sorted_rows = sorted(normalized_rows, key=lambda item: item[0])
    cumulative = 0
    series: list[RegistrationStatPoint] = []
    for period_start, count in sorted_rows:
        cumulative += count
        series.append(
            RegistrationStatPoint(
                period=period_start.date().isoformat(),
                label=_format_label(period_start, granularity),
                count=count,
                cumulative=cumulative,
            ),
        )

    counts = [count for _, count in sorted_rows]
    total_in_range = sum(counts)

    if granularity == "month":
        current = counts[-1] if counts else 0
        previous = counts[-2] if len(counts) > 1 else 0
        growth_label = "vs bulan lepas"
    elif granularity == "week":
        current = counts[-1] if counts else 0
        previous = counts[-2] if len(counts) > 1 else 0
        growth_label = "vs minggu lepas"
    else:
        current = total_in_range
        if from_date and to_date:
            span_days = (to_date - from_date).days + 1
            prev_end = from_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=span_days - 1)
            previous = sum(
                count
                for period_start, count in sorted_rows
                if prev_start <= period_start.date() <= prev_end
            )
            # For custom range, rows may only include in-range; previous from separate query
            growth_label = "vs tempoh sebelumnya"
        else:
            previous = counts[-2] if len(counts) > 1 else 0
            growth_label = "vs tempoh sebelumnya"

    return RegistrationStatsData(
        series=series,
        growth_percent=compute_growth_percent(current, previous),
        growth_label=growth_label,
        total_in_range=total_in_range,
    )


def build_registration_stats_with_previous(
    in_range_rows: list[tuple[datetime | str, int]],
    previous_total: int,
    *,
    granularity: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> RegistrationStatsData:
    stats = build_registration_stats(
        in_range_rows,
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )
    if granularity == "custom" and from_date and to_date:
        current = stats.total_in_range
        stats.growth_percent = compute_growth_percent(current, previous_total)
    return stats


def _format_label(period_start: datetime, granularity: str) -> str:
    if granularity == "month":
        return period_start.strftime("%b %Y")
    if granularity == "week":
        iso = period_start.isocalendar()
        return f"W{iso.week:02d} {iso.year}"
    return period_start.strftime("%d %b %Y")


def _growth_label(granularity: str) -> str:
    if granularity == "month":
        return "vs bulan lepas"
    if granularity == "week":
        return "vs minggu lepas"
    return "vs tempoh sebelumnya"


def default_stats_range(granularity: str) -> tuple[date, date]:
    today = datetime.now(UTC).date()
    if granularity == "month":
        start = today.replace(day=1) - timedelta(days=365)
        return start, today
    if granularity == "week":
        start = today - timedelta(weeks=12)
        return start, today
    return today - timedelta(days=30), today


def _normalize_period(period: datetime | str, granularity: str) -> datetime:
    if isinstance(period, datetime):
        return period if period.tzinfo else period.replace(tzinfo=UTC)

    if granularity == "month":
        year, month = period.split("-")
        return datetime(int(year), int(month), 1, tzinfo=UTC)
    if granularity == "week":
        year_str, week_str = period.split("-")
        return datetime.fromisocalendar(int(year_str), int(week_str), 1).replace(
            tzinfo=UTC,
        )
    year, month, day = period.split("-")
    return datetime(int(year), int(month), int(day), tzinfo=UTC)
