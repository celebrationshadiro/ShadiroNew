from __future__ import annotations

import argparse
import os
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean seeded test data safely.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete data. Without this flag, script runs in dry-run mode.",
    )
    parser.add_argument(
        "--purge-categories",
        action="store_true",
        help="Also delete seeded vendor categories (cat-*) created by seed script.",
    )
    return parser.parse_args()


def count_and_delete(collection, query: dict[str, Any], apply: bool) -> tuple[int, int]:
    count = collection.count_documents(query)
    deleted = 0
    if apply and count > 0:
        deleted = collection.delete_many(query).deleted_count
    return count, deleted


def main() -> None:
    args = parse_args()
    load_dotenv("backend/.env")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")
    if not mongo_url or not db_name:
        raise RuntimeError("Missing MONGO_URL or DB_NAME in backend/.env")

    client = MongoClient(mongo_url)
    db = client[db_name]

    apply = args.apply
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"Running cleanup mode: {mode}")

    test_user_email_query = {"email": {"$regex": r"^(vendor\..*@test\.com|customer[0-9]+@test\.com)$"}}
    user_docs = list(db.users.find(test_user_email_query, {"_id": 0, "id": 1, "email": 1}))
    user_ids = [u["id"] for u in user_docs]

    vendor_docs = list(db.vendors.find({"user_id": {"$in": user_ids}}, {"_id": 0, "id": 1, "user_id": 1}))
    vendor_ids = [v["id"] for v in vendor_docs]

    report: list[tuple[str, int, int]] = []

    queries = {
        "quotes": {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"vendor_id": {"$in": vendor_ids}},
                {"id": {"$regex": r"^q_"}},
            ]
        },
        "bookings": {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"vendor_id": {"$in": vendor_ids}},
                {"id": {"$regex": r"^bk_"}},
            ]
        },
        "orders": {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"vendor_id": {"$in": vendor_ids}},
                {"id": {"$regex": r"^ord_"}},
            ]
        },
        "payments": {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"vendor_id": {"$in": vendor_ids}},
                {"id": {"$regex": r"^pay_"}},
                {"order_id": {"$regex": r"^ord_"}},
            ]
        },
        "events": {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"id": {"$regex": r"^evt_"}},
            ]
        },
        "vendor_ledger": {
            "$or": [
                {"vendor_id": {"$in": vendor_ids}},
                {"id": {"$regex": r"^led_"}},
                {"reference_id": {"$regex": r"^ord_"}},
            ]
        },
        "vendors": {"user_id": {"$in": user_ids}},
        "users": test_user_email_query,
    }

    for collection_name, query in queries.items():
        collection = db[collection_name]
        count, deleted = count_and_delete(collection, query, apply)
        report.append((collection_name, count, deleted))

    if args.purge_categories:
        category_query = {"id": {"$in": [
            "cat-grocery",
            "cat-entertainment",
            "cat-catering",
            "cat-decor",
            "cat-venues",
            "cat-makeup",
            "cat-photography",
            "cat-transport",
            "cat-mehandi",
        ]}}
        count, deleted = count_and_delete(db.vendor_categories, category_query, apply)
        report.append(("vendor_categories", count, deleted))

    print("\nCleanup report:")
    for name, count, deleted in report:
        print(f"- {name}: matched={count}, deleted={deleted}")

    if not apply:
        print("\nNo data deleted (dry-run). Re-run with --apply to execute cleanup.")


if __name__ == "__main__":
    main()
