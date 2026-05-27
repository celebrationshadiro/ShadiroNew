from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int
    skip: int
    limit: int


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    skip: int | None = Query(default=None, ge=0),
    limit: int | None = Query(default=None, ge=1, le=100),
) -> Pagination:
    resolved_limit = limit or page_size
    if resolved_limit > 50:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Pagination limit exceeds maximum allowed limit of 50 items per page"
        )
    resolved_skip = skip if skip is not None else (page - 1) * resolved_limit
    resolved_page = (resolved_skip // resolved_limit) + 1
    return Pagination(
        page=resolved_page,
        page_size=resolved_limit,
        skip=resolved_skip,
        limit=resolved_limit,
    )
