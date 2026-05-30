def success(data) -> dict:
    """Success response: {"data": ...}"""
    return {"data": data}


def paginated(data, page: int, limit: int, total: int) -> dict:
    """Paginated response: {"data": [...], "pagination": {...}}"""
    return {
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total},
    }
