from __future__ import annotations

from datetime import datetime

from sqlalchemy import ColumnElement, func
from sqlalchemy.ext.asyncio import AsyncSession


def period_expression(
    column: ColumnElement[datetime],
    granularity: str,
    *,
    dialect_name: str,
) -> ColumnElement:
    if dialect_name == "postgresql":
        trunc_unit = (
            "month"
            if granularity == "month"
            else "week"
            if granularity == "week"
            else "day"
        )
        return func.date_trunc(trunc_unit, column)

    if granularity == "month":
        return func.strftime("%Y-%m", column)
    if granularity == "week":
        return func.strftime("%Y-%W", column)
    return func.strftime("%Y-%m-%d", column)


async def get_dialect_name(db: AsyncSession) -> str:
    bind = db.get_bind()
    return bind.dialect.name if bind is not None else "postgresql"
