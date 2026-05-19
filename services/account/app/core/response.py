def success(data) -> dict:
    return {"data": data}


def paginated(data, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total},
    }
