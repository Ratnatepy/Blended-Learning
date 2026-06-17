"""Simple Streamlit admin authentication component."""

from __future__ import annotations

import streamlit as st

from components.assets import icon_title


def require_admin_login(admin_email: str, admin_password: str) -> bool:
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if st.session_state["admin_logged_in"]:
        st.sidebar.success("Admin logged in")
        if st.sidebar.button("Logout Admin"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
        return True

    st.markdown(icon_title("lock", "Admin Login Required", level=3), unsafe_allow_html=True)
    st.info("Please log in to access the Admin dashboard.")

    with st.form("admin_login_form"):
        email = st.text_input("Admin Email")
        password = st.text_input("Admin Password", type="password")
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if email == admin_email and password == admin_password:
            st.session_state["admin_logged_in"] = True
            st.success("Admin login successful.")
            st.rerun()
        else:
            st.error("Invalid admin email or password.")

    return False
