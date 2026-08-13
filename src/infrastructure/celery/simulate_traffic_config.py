
import hashlib

# Pareto 80/20 — 20% phim được coi là "Trending"
TRENDING_RATIO = 0.1

# Xác suất user chọn phim Trending HOẶC đúng "gu" (preferred category)
PREFERENCE_WEIGHT = 0.9

# Tỷ lệ % thời lượng xem khi phim ĐÚNG gu/trending
HIGH_WATCH_RATIO_RANGE = (0.8, 1.0)
# Tỷ lệ % thời lượng xem khi phim KHÔNG đúng gu
LOW_WATCH_RATIO_RANGE = (0.1, 0.3)

# Hệ thống chưa lưu total_duration cho từng episode -> giả định độ dài
# trung bình để quy đổi % thành số giây thực tế.
ASSUMED_FULL_DURATION_SECONDS = 5400  # 90 phút


def get_preferred_category_id(user_id: str, category_ids: list[str]) -> str | None:
    """
    Gán "gu" cho user_id theo cách HOÀN TOÀN xác định (deterministic) —
    cùng 1 user_id luôn ra cùng 1 category ở mọi lần chạy task, KHÔNG cần
    lưu cache vào Redis/DB. Đây là dạng "config cứng" thực dụng: vì
    category_id là UUID sinh động từ DB (không biết trước để hardcode tay),
    và có ~1000 user giả lập (không thể liệt kê thủ công từng người),
    hash-based mapping đóng vai trò cấu hình cố định, tái lập được 100%.
    """
    if not category_ids:
        return None
    digest = hashlib.md5(user_id.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(category_ids)
    return category_ids[idx]