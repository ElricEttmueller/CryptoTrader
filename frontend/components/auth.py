import streamlit as st
import requests
from typing import Optional
import json

class AuthComponent:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'user_token' not in st.session_state:
            st.session_state.user_token = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None

    def login_form(self) -> Optional[dict]:
        """Display login form and handle login logic."""
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                try:
                    response = requests.post(
                        f"{self.api_base_url}/auth/token",
                        data={"username": email, "password": password}
                    )
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state.user_token = token_data["access_token"]
                        st.success("Successfully logged in!")
                        return token_data
                    else:
                        st.error("Invalid email or password")
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
        return None

    def register_form(self) -> Optional[dict]:
        """Display registration form and handle registration logic."""
        with st.form("register_form"):
            st.subheader("Register")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            full_name = st.text_input("Full Name (Optional)")
            submitted = st.form_submit_button("Register")

            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match")
                    return None

                try:
                    response = requests.post(
                        f"{self.api_base_url}/auth/register",
                        json={
                            "email": email,
                            "password": password,
                            "full_name": full_name or None
                        }
                    )
                    if response.status_code == 200:
                        st.success("Registration successful! Please login.")
                        return response.json()
                    else:
                        st.error(response.json().get("detail", "Registration failed"))
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
        return None

    def api_key_management(self):
        """Display API key management interface."""
        if not st.session_state.user_token:
            st.warning("Please login to manage API keys")
            return

        st.subheader("API Key Management")

        # Add new API key
        with st.form("add_api_key"):
            st.write("Add New API Key")
            key_name = st.text_input("Key Name")
            api_key = st.text_input("API Key")
            api_secret = st.text_input("API Secret", type="password")
            exchange = st.selectbox("Exchange", ["binance", "coinbase", "kraken"])
            permissions = st.multiselect(
                "Permissions",
                ["read", "trade", "withdraw"],
                default=["read"]
            )
            submitted = st.form_submit_button("Add API Key")

            if submitted:
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
                    response = requests.post(
                        f"{self.api_base_url}/auth/api-keys",
                        headers=headers,
                        json={
                            "key_name": key_name,
                            "api_key": api_key,
                            "api_secret": api_secret,
                            "exchange": exchange,
                            "permissions": permissions
                        }
                    )
                    if response.status_code == 200:
                        st.success("API key added successfully!")
                    else:
                        st.error(response.json().get("detail", "Failed to add API key"))
                except Exception as e:
                    st.error(f"Failed to add API key: {str(e)}")

        # List existing API keys
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
            response = requests.get(
                f"{self.api_base_url}/auth/api-keys",
                headers=headers
            )
            if response.status_code == 200:
                api_keys = response.json()
                if api_keys:
                    st.write("Your API Keys:")
                    for key in api_keys:
                        with st.expander(f"{key['key_name']} ({key['exchange']})"):
                            st.write(f"Permissions: {', '.join(key['permissions'])}")
                            st.write(f"Created: {key['created_at']}")
                else:
                    st.info("No API keys found")
        except Exception as e:
            st.error(f"Failed to fetch API keys: {str(e)}")

    def logout(self):
        """Handle user logout."""
        if st.button("Logout"):
            st.session_state.user_token = None
            st.session_state.user_info = None
            st.success("Logged out successfully!")
            st.experimental_rerun()

    def render(self):
        """Render the authentication interface."""
        if not st.session_state.user_token:
            tab1, tab2 = st.tabs(["Login", "Register"])
            with tab1:
                self.login_form()
            with tab2:
                self.register_form()
        else:
            st.sidebar.success("Logged in")
            self.logout()
            self.api_key_management()
