"""
YouTube API wrapper - beheert verbindingen voor beide accounts
"""

import os
import json
import pickle
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTubeAccount:
    """Beheert één YouTube account verbinding"""

    def __init__(self, account_key: str, settings_manager):
        self.account_key = account_key
        self.sm = settings_manager
        self.data_dir = settings_manager.get_data_dir()
        self.service = None
        self._credentials = None

    @property
    def config(self) -> dict:
        return self.sm.get("accounts", self.account_key) or {}

    @property
    def name(self) -> str:
        return self.config.get("name", self.account_key)

    @property
    def credentials_file(self) -> Path:
        return self.data_dir / self.config.get("credentials_file", f"credentials_{self.account_key}.json")

    @property
    def token_file(self) -> Path:
        return self.data_dir / self.config.get("token_file", f"token_{self.account_key}.json")

    def is_credentials_available(self) -> bool:
        return self.credentials_file.exists()

    def is_authenticated(self) -> bool:
        return self.token_file.exists() and self.service is not None

    def authenticate(self, url_callback=None) -> bool:
        """Start OAuth2 flow en sla token op. Geeft True terug bij succes."""
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"Geen credentials bestand gevonden voor {self.name}.\n"
                f"Verwacht: {self.credentials_file}\n"
                f"Download dit via Google Cloud Console."
            )

        creds = None

        # Probeer bestaand token te laden
        if self.token_file.exists():
            try:
                with open(self.token_file, "rb") as f:
                    creds = pickle.load(f)
            except Exception:
                creds = None

        # Ververs token als verlopen
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        # Nieuw token aanmaken via browser
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_file), 
                SCOPES
            )
            
            if url_callback:
                # Als we een callback hebben, genereren we eerst de URL
                # Gebruik een vaste 'state' om de (mismatching_state) CSRF error te voorkomen.
                # Dit is nodig omdat run_local_server intern authorization_url() opnieuw aanroept.
                import secrets
                state = secrets.token_urlsafe(16)

                flow.redirect_uri = "http://localhost:8080/"
                auth_url, _ = flow.authorization_url(prompt='consent', state=state)
                url_callback(auth_url)
                
                # Start de server met dezelfde state en prompt instellingen
                creds = flow.run_local_server(
                    host='localhost', 
                    port=8080, 
                    open_browser=False, 
                    state=state,
                    prompt='consent'
                )
            else:
                # Standaard flow
                creds = flow.run_local_server(port=0, open_browser=True)

        # Token opslaan
        with open(self.token_file, "wb") as f:
            pickle.dump(creds, f)

        self._credentials = creds
        self.service = build("youtube", "v3", credentials=creds, static_discovery=False)
        return True

    def connect(self) -> bool:
        """Verbind met bestaand token, zonder browser. Geeft False als login nodig is."""
        if not self.token_file.exists():
            return False

        try:
            with open(self.token_file, "rb") as f:
                creds = pickle.load(f)

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_file, "wb") as f:
                    pickle.dump(creds, f)

            if creds.valid:
                self._credentials = creds
                self.service = build("youtube", "v3", credentials=creds, static_discovery=False)
                return True
        except Exception:
            pass

        return False

    def get_channel_info(self) -> Optional[dict]:
        """Haal kanaalinformatie op"""
        if not self.service:
            return None
        try:
            resp = self.service.channels().list(part="snippet,statistics", mine=True).execute()
            items = resp.get("items", [])
            return items[0] if items else None
        except HttpError:
            return None

    def get_stream_keys(self) -> list:
        """Haal beschikbare streamkeys op"""
        if not self.service:
            return []
        try:
            resp = self.service.liveStreams().list(
                part="snippet,cdn,status", mine=True, maxResults=50
            ).execute()
            return resp.get("items", [])
        except HttpError:
            return []

    def create_broadcast(
        self,
        title: str,
        description: str,
        scheduled_start: datetime,
        privacy: str = "public",
        made_for_kids: bool = False,
        enable_dvr: bool = True,
        record_from_start: bool = True,
        latency_preference: str = "normal",
    ) -> Optional[dict]:
        """Maak een nieuwe broadcast aan"""
        if not self.service:
            raise RuntimeError("Niet ingelogd")

        # Zet tijdzone-bewuste datetime om naar UTC ISO string
        if scheduled_start.tzinfo is None:
            from zoneinfo import ZoneInfo
            scheduled_start = scheduled_start.replace(tzinfo=ZoneInfo("Europe/Amsterdam"))

        start_iso = scheduled_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": start_iso,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": made_for_kids,
            },
            "contentDetails": {
                "enableDvr": enable_dvr,
                "recordFromStart": record_from_start,
                "latencyPreference": latency_preference,
                "monitorStream": {
                    "enableMonitorStream": False,
                },
            },
        }

        return self.service.liveBroadcasts().insert(
            part="snippet,status,contentDetails", body=body
        ).execute()

    def bind_broadcast_to_stream(self, broadcast_id: str, stream_id: str) -> dict:
        """Koppel broadcast aan streamkey"""
        if not self.service:
            raise RuntimeError("Niet ingelogd")
        return self.service.liveBroadcasts().bind(
            part="id,contentDetails",
            id=broadcast_id,
            streamId=stream_id,
        ).execute()

    def get_broadcasts(
        self,
        broadcast_status: str = "all",
        max_results: int = 50,
        page_token: str = None,
    ) -> dict:
        """Haal broadcasts op"""
        if not self.service:
            return {"items": []}
        try:
            params = {
                "part": "snippet,status,contentDetails",
                "mine": True,
                "maxResults": max_results,
                "broadcastStatus": broadcast_status,
            }
            if page_token:
                params["pageToken"] = page_token

            return self.service.liveBroadcasts().list(**params).execute()
        except HttpError as e:
            print(f"Fout bij ophalen broadcasts: {e}")
            return {"items": []}

    def get_all_old_broadcasts(self, days: int = 180) -> list:
        """Haal alle broadcasts op die ouder zijn dan X dagen"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        old_broadcasts = []
        page_token = None

        while True:
            resp = self.get_broadcasts(
                broadcast_status="completed",
                max_results=50,
                page_token=page_token,
            )
            for item in resp.get("items", []):
                snippet = item.get("snippet", {})
                status = item.get("status", {})

                # Sla al verborgen/niet-gelistede items over
                if status.get("privacyStatus") in ("private", "unlisted"):
                    continue

                start_time = snippet.get("actualStartTime") or snippet.get("scheduledStartTime")
                if start_time:
                    try:
                        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        if dt < cutoff:
                            old_broadcasts.append(item)
                    except Exception:
                        pass

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return old_broadcasts

    def set_broadcast_privacy(self, broadcast_id: str, privacy: str) -> Optional[dict]:
        """Verander privacy status van een broadcast"""
        if not self.service:
            raise RuntimeError("Niet ingelogd")
        try:
            body = {
                "id": broadcast_id,
                "status": {"privacyStatus": privacy},
            }
            return self.service.liveBroadcasts().update(
                part="status", body=body
            ).execute()
        except HttpError as e:
            print(f"Fout bij updaten broadcast {broadcast_id}: {e}")
            return None

    def update_broadcast(self, broadcast_id: str, title: str = None, description: str = None) -> Optional[dict]:
        """Update titel en/of omschrijving van een broadcast"""
        if not self.service:
            raise RuntimeError("Niet ingelogd")

        # Eerst huidige waarden ophalen
        resp = self.service.liveBroadcasts().list(
            part="snippet", id=broadcast_id
        ).execute()
        items = resp.get("items", [])
        if not items:
            return None

        snippet = items[0]["snippet"]
        if title:
            snippet["title"] = title
        if description is not None:
            snippet["description"] = description

        body = {"id": broadcast_id, "snippet": snippet}
        return self.service.liveBroadcasts().update(part="snippet", body=body).execute()


class YouTubeManager:
    """Beheert beide YouTube accounts"""

    def __init__(self, settings_manager):
        self.sm = settings_manager
        self.accounts = {
            "main": YouTubeAccount("main", settings_manager),
            "tolk": YouTubeAccount("tolk", settings_manager),
        }

    def get_account(self, key: str) -> YouTubeAccount:
        return self.accounts.get(key)

    def connect_all(self):
        """Probeer alle accounts stil in te loggen"""
        for acc in self.accounts.values():
            if self.sm.get("accounts", acc.account_key, "enabled"):
                acc.connect()

    @property
    def main(self) -> YouTubeAccount:
        return self.accounts["main"]

    @property
    def tolk(self) -> YouTubeAccount:
        return self.accounts["tolk"]
