# MIT License - Copyright (c) 2026 eripum9

def metadata_source_summary(state, config):
    state = state if isinstance(state, dict) else {}
    config = config if isinstance(config, dict) else {}
    track = state.get("track") if isinstance(state.get("track"), dict) else {}
    privacy = state.get("privacy") if isinstance(state.get("privacy"), dict) else {}
    amazon = state.get("amazon_devtools") if isinstance(state.get("amazon_devtools"), dict) else {}
    notification = state.get("notification") if isinstance(state.get("notification"), dict) else None

    if privacy.get("hidden") or config.get("privacy_private_session"):
        return {
            "label": "プライベート",
            "detail": privacy.get("reason") or "プライベートセッションが有効です",
            "state": "warn",
        }

    track_status = str(track.get("status") or "").lower()
    if track_status == "paused":
        return {
            "label": "一時停止中",
            "detail": track.get("title") or "再生は一時停止中です",
            "state": "warn",
        }

    if config.get("amazon_devtools_enabled") and amazon.get("status") == "found":
        return {
            "label": "Amazonメタデータ",
            "detail": amazon.get("title") or track.get("title") or "Amazon Musicのメタデータを使用中",
            "state": "good",
        }

    if notification and config.get("notification_enrichment_enabled"):
        return {
            "label": "通知(フォールバック)",
            "detail": notification.get("title") or "Amazon Musicの通知を使用中",
            "state": "good",
        }

    if track:
        return {
            "label": "SMTC(フォールバック)",
            "detail": track.get("title") or "Windowsのメディアセッションデータを使用中",
            "state": "good" if track_status == "playing" else "muted",
        }

    if config.get("amazon_devtools_enabled"):
        devtools_status = str(amazon.get("status") or "waiting").lower()
        if devtools_status in ("error", "unavailable"):
            return {
                "label": "利用不可",
                "detail": amazon.get("detail") or "Amazon Musicのメタデータが利用できません",
                "state": "bad",
            }
        return {
            "label": "待機中",
            "detail": amazon.get("detail") or "Amazon Musicのメタデータを待機中",
            "state": "warn",
        }

    return {
        "label": "待機中",
        "detail": "Amazon Musicを待機中",
        "state": "muted",
    }
