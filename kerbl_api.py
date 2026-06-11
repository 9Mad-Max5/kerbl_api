import requests
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode


class KerblClient:
    # Production URLs
    PROD_URL = "https://backend.kerbl-iot.com"
    DEV_URL = "https://backend.dev.kerbl-iot.com"
    API_VERSION = "/api/v0.1"
    WS_VERSION = "/ws/v0.1/socket.io"

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = PROD_URL,
        environment: str = "prod",
    ):
        self.base_url = base_url
        self.api_base = f"{base_url}{self.API_VERSION}"
        self.environment = environment
        self.email = email
        self.password = password

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: float = 0

        self.session = requests.Session()

    # ---------------------------
    # AUTH ENDPOINTS
    # ---------------------------

    def login(self) -> None:
        """Sign in with email and password"""
        url = f"{self.api_base}/auth/sign-in"
        payload = {"email": self.email, "password": self.password}
        
        r = self.session.post(url, json=payload)
        r.raise_for_status()
        self._store_tokens(r.json())

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Create new account"""
        url = f"{self.api_base}/auth/sign-up"
        payload = {"email": email, "password": password}
        
        r = self.session.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def refresh(self) -> None:
        """Refresh access token"""
        if not self.refresh_token:
            raise RuntimeError("No refresh token available")

        url = f"{self.api_base}/auth/refresh"
        payload = {"refreshToken": self.refresh_token}
        
        r = self.session.post(url, json=payload)
        r.raise_for_status()
        self._store_tokens(r.json())

    def verify_token(self) -> Dict[str, Any]:
        """Verify current token"""
        url = f"{self.api_base}/auth/verify"
        return self.request("GET", "/auth/verify")

    def _store_tokens(self, data: Dict[str, Any]) -> None:
        """Store authentication tokens"""
        self.access_token = data.get("accessToken")
        self.refresh_token = data.get("refreshToken")
        
        expires_in = data.get("expiresIn", 3600)
        self.token_expiry = time.time() + expires_in - 30
        
        if not self.access_token:
            raise RuntimeError("Login failed: no access token received")

    def _ensure_token(self) -> None:
        """Auto refresh if needed"""
        if not self.access_token:
            self.login()
        elif time.time() >= self.token_expiry:
            self.refresh()

    # ---------------------------
    # REQUEST HANDLER
    # ---------------------------

    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request"""
        self._ensure_token()

        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        r = self.session.request(method, url, headers=headers, **kwargs)

        # Auto-retry on token expiry
        if r.status_code == 401:
            self.refresh()
            headers["Authorization"] = f"Bearer {self.access_token}"
            r = self.session.request(method, url, headers=headers, **kwargs)

        r.raise_for_status()
        
        return r.json() if r.text else {}

    # ---------------------------
    # DEVICE ENDPOINTS
    # ---------------------------

    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device by ID"""
        return self.request("GET", f"/device/{device_id}")

    def get_device_demo(self, device_id: str) -> Dict[str, Any]:
        """Get device demo mode"""
        return self.request("GET", f"/device/{device_id}/demo")

    # ---------------------------
    # SMART COOP ENDPOINTS
    # ---------------------------

    def get_coop(self, coop_id: str) -> Dict[str, Any]:
        """Get smart coop device"""
        return self.get_device(coop_id)

    def get_coop_log(self, coop_id: str) -> Dict[str, Any]:
        """Get coop event log"""
        return self.request("GET", f"/device/smart-coop/{coop_id}/log")

    def get_coop_events(
        self,
        coop_id: str,
        page_timestamp: Optional[int] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        level: Optional[str] = None,
        confirmed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get coop events with optional filtering and pagination"""
        endpoint = f"/device/smart-coop/{coop_id}/events"
        params = {}
        
        if from_time and to_time:
            params["from"] = from_time
            params["to"] = to_time
        if level:
            params["level"] = level
        if confirmed is not None:
            params["confirmed"] = str(confirmed).lower()
        if page_timestamp is not None:
            params["pagetimestamp"] = page_timestamp
        
        if params:
            endpoint += f"?{urlencode(params)}"
        
        return self.request("GET", endpoint)

    def confirm_coop_events(self, coop_id: str) -> Dict[str, Any]:
        """Confirm coop events"""
        return self.request("POST", f"/device/smart-coop/{coop_id}/events/confirm", json={})

    def delete_coop_event(self, coop_id: str) -> Dict[str, Any]:
        """Delete coop event"""
        return self.request("POST", f"/device/smart-coop/{coop_id}/events/delete", json={})

    def delete_all_coop_events(self, coop_id: str, confirmed: Optional[bool] = None) -> Dict[str, Any]:
        """Delete all coop events"""
        endpoint = f"/device/smart-coop/{coop_id}/events/delete-all"
        if confirmed is not None:
            endpoint += f"?confirmed={str(confirmed).lower()}"
        return self.request("POST", endpoint, json={})

    def send_coop_command(self, coop_id: str, command: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send command to smart coop"""
        return self.request(
            "POST",
            f"/device/smart-coop/{coop_id}/command/{command}",
            json=data or {}
        )

    def set_coop_parameter(self, coop_id: str, parameter: str, value: Any) -> Dict[str, Any]:
        """Set coop parameter"""
        return self.request(
            "POST",
            f"/device/smart-coop/{coop_id}/parameter/{parameter}",
            json={"value": value}
        )

    def refresh_coop(self, coop_id: str) -> Dict[str, Any]:
        """Refresh coop state"""
        return self.request("POST", f"/device/smart-coop/{coop_id}/refresh", json={})

    def get_coop_continuous_values(
        self,
        coop_id: str,
        metric: str,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get continuous values (temperature, etc.)"""
        endpoint = f"/device/smart-coop/{coop_id}/continuous-values/{metric}"
        
        if from_time and to_time:
            endpoint += f"?from={from_time}&to={to_time}"
        
        return self.request("GET", endpoint)

    def reset_coop_desired_state(self, coop_id: str) -> Dict[str, Any]:
        """Reset coop desired state"""
        return self.request("POST", f"/device/smart-coop/{coop_id}/reset-desired-state", json={})

    # ---------------------------
    # SMART ENERGIZER ENDPOINTS
    # ---------------------------

    def get_energizer(self, energizer_id: str) -> Dict[str, Any]:
        """Get smart energizer device"""
        return self.get_device(energizer_id)

    def get_energizer_events(
        self,
        energizer_id: str,
        page_timestamp: Optional[int] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        level: Optional[str] = None,
        confirmed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get energizer events"""
        endpoint = f"/device/smart-energizer/{energizer_id}/events"
        params = {}
        
        if from_time and to_time:
            params["from"] = from_time
            params["to"] = to_time
        if level:
            params["level"] = level
        if confirmed is not None:
            params["confirmed"] = str(confirmed).lower()
        if page_timestamp is not None:
            params["pagetimestamp"] = page_timestamp
        
        if params:
            endpoint += f"?{urlencode(params)}"
        
        return self.request("GET", endpoint)

    def send_energizer_command(self, energizer_id: str, command: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send command to smart energizer"""
        return self.request(
            "POST",
            f"/device/smart-energizer/{energizer_id}/command/{command}",
            json=data or {}
        )

    # ---------------------------
    # SMART SATELLITE ENDPOINTS
    # ---------------------------

    def get_satellite(self, satellite_id: str) -> Dict[str, Any]:
        """Get smart satellite device"""
        return self.get_device(satellite_id)

    def get_satellite_events(
        self,
        satellite_id: str,
        page_timestamp: Optional[int] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        level: Optional[str] = None,
        confirmed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get satellite events"""
        endpoint = f"/device/smart-satellite/{satellite_id}/events"
        params = {}
        
        if from_time and to_time:
            params["from"] = from_time
            params["to"] = to_time
        if level:
            params["level"] = level
        if confirmed is not None:
            params["confirmed"] = str(confirmed).lower()
        if page_timestamp is not None:
            params["pagetimestamp"] = page_timestamp
        
        if params:
            endpoint += f"?{urlencode(params)}"
        
        return self.request("GET", endpoint)

    def send_satellite_command(self, satellite_id: str, command: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send command to smart satellite"""
        return self.request(
            "POST",
            f"/device/smart-satellite/{satellite_id}/command/{command}",
            json=data or {}
        )

    # ---------------------------
    # SMART CHICKENDOOR ENDPOINTS
    # ---------------------------

    def get_chickendoor(self, chickendoor_id: str) -> Dict[str, Any]:
        """Get smart chickendoor device"""
        return self.get_device(chickendoor_id)

    def get_chickendoor_events(
        self,
        chickendoor_id: str,
        page_timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get chickendoor events"""
        endpoint = f"/device/smart-chickendoor/{chickendoor_id}/events"
        
        if page_timestamp is not None:
            endpoint += f"?pagetimestamp={page_timestamp}"
        
        return self.request("GET", endpoint)

    def send_chickendoor_command(self, chickendoor_id: str, command: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send command to smart chickendoor"""
        return self.request(
            "POST",
            f"/device/smart-chickendoor/{chickendoor_id}/command/{command}",
            json=data or {}
        )

    def get_chickendoor_pending_commands(self, chickendoor_id: str) -> Dict[str, Any]:
        """Get pending commands for chickendoor"""
        return self.request("GET", f"/device/smart-chickendoor/{chickendoor_id}/pending-commands")

    # ---------------------------
    # SMART TRACKER ENDPOINTS
    # ---------------------------

    def get_smart_tracker_continuous_values(
        self,
        tracker_id: str,
        metric: str,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get smart tracker continuous values"""
        endpoint = f"/device/smart-tracker/{tracker_id}/continuous-values/{metric}"
        
        if from_time and to_time:
            endpoint += f"?from={from_time}&to={to_time}"
        
        return self.request("GET", endpoint)

    # ---------------------------
    # DATA ENDPOINTS
    # ---------------------------

    def get_continuous_values(
        self,
        device_type: str,
        device_id: str,
        metric: str,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get continuous values for any device"""
        endpoint = f"/data/{device_type}/{device_id}/{metric}"
        
        if from_time and to_time:
            endpoint += f"?from={from_time}&to={to_time}"
        
        return self.request("GET", endpoint)

    # ---------------------------
    # USER ENDPOINTS
    # ---------------------------

    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        return self.request("GET", "/user/profile-picture")

    def get_prepaid_balance(self) -> Dict[str, Any]:
        """Get prepaid account balance"""
        return self.request("GET", "/user/prepaid-account/balance")

    def reset_password(self) -> Dict[str, Any]:
        """Request password reset"""
        return self.request("POST", "/user/reset-password", json={})

    def confirm_email(self, token: str) -> Dict[str, Any]:
        """Confirm email with token"""
        return self.request("POST", "/user/confirm-email", json={"token": token})

    # ---------------------------
    # UTILITY ENDPOINTS
    # ---------------------------

    def ping(self) -> Dict[str, Any]:
        """Ping maintenance endpoint"""
        return self.request("GET", "/maintenance/ping")

    def get_deployed_branch(self) -> Dict[str, Any]:
        """Get deployed branch info"""
        return self.request("GET", "/maintenance/deployed_branch")


# ---------------------------
# EXAMPLE USAGE
# ---------------------------

if __name__ == "__main__":
    from credentials import mail, password
    
    client = KerblClient(
        email=mail,
        password=password,
        base_url=KerblClient.PROD_URL,
    )

    # Login
    client.login()
    print("✓ Logged in")

    # Get device
    # device = client.get_device("DEVICE_ID")
    # print(f"Device: {device}")

    # Get coop info
    # coop = client.get_coop("COOP_ID")
    # print(f"Coop: {coop}")

    # Get coop log
    # log = client.get_coop_log("COOP_ID")
    # print(f"Log: {log}")

    # Get coop events with time range
    # events = client.get_coop_events(
    #     "COOP_ID",
    #     from_time="2024-01-01T00:00:00Z",
    #     to_time="2024-01-02T00:00:00Z",
    # )
    # print(f"Events: {events}")

    # Send command to coop
    # result = client.send_coop_command("COOP_ID", "openDoor")
    # print(f"Command result: {result}")

    # Get continuous values (temperature, etc.)
    # values = client.get_coop_continuous_values(
    #     "COOP_ID",
    #     "AIR_TEMPERATURE",
    #     from_time="2024-01-01T00:00:00Z",
    #     to_time="2024-01-02T00:00:00Z",
    # )
    # print(f"Values: {values}")

    # Maintenance ping
    # ping = client.ping()
    # print(f"Ping: {ping}")
