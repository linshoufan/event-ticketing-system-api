def success(data) -> dict:
    """成功回應：{"data": ...}"""
    return {"data": data}


def paginated(data, page: int, limit: int, total: int) -> dict:
    """分頁回應：{"data": [...], "pagination": {...}}"""
    return {
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total},
    }