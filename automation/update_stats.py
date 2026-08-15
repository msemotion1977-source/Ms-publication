"""
Met à jour le nombre d'abonnés de chaque chaîne connectée, chaque semaine.

Important, honnêtement : il n'existe pas d'API publique gratuite qui donne les revenus
publicitaires en temps réel.
- YouTube expose bien une "YouTube Analytics Monetary API", mais elle nécessite une
  demande d'accès séparée à Google (audit "revenue data"), pas activée par défaut.
- TikTok Creator Fund / Creativity Program n'a pas d'API publique de revenus du tout.
Ce script remplit donc automatiquement les abonnés (ça, c'est 100% automatisable et gratuit),
et laisse revenue_cents à 0 par défaut : à toi de le corriger à la main directement dans la
table Supabase "stats_weekly" (Table Editor, gratuit, 2 clics) si tu veux suivre tes revenus
réels dans le dashboard.
"""
import requests
from datetime import date, timedelta
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def monday_of_this_week() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def get_youtube_subscribers(access_token: str, external_channel_id: str) -> int:
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "statistics", "id": external_channel_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return 0
    return int(items[0]["statistics"].get("subscriberCount", 0))


def get_tiktok_followers(access_token: str) -> int:
    resp = requests.get(
        "https://open.tiktokapis.com/v2/user/info/",
        params={"fields": "follower_count"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("user", {}).get("follower_count", 0)


def main():
    week_start = monday_of_this_week().isoformat()
    channels = supabase.table("channels").select("*").execute().data

    for channel in channels:
        if not channel.get("oauth_access_token"):
            continue
        try:
            if channel["platform"] == "youtube":
                subs = get_youtube_subscribers(channel["oauth_access_token"], channel["external_channel_id"])
            else:
                subs = get_tiktok_followers(channel["oauth_access_token"])
        except Exception as e:
            print(f"Impossible de récupérer les stats pour {channel['display_name']} : {e}")
            continue

        previous = (
            supabase.table("stats_weekly")
            .select("*")
            .eq("channel_id", channel["id"])
            .order("week_start", desc=True)
            .limit(1)
            .execute()
            .data
        )
        prev_subs = previous[0]["subscribers"] if previous else subs

        supabase.table("stats_weekly").upsert({
            "channel_id": channel["id"],
            "week_start": week_start,
            "subscribers": subs,
            "subscribers_gained": max(subs - prev_subs, 0),
        }, on_conflict="channel_id,week_start").execute()
        print(f"{channel['display_name']} : {subs} abonnés")


if __name__ == "__main__":
    main()
