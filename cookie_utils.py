import extra_streamlit_components as stx


def get_cookie_manager():
    """Return a fresh CookieManager each script run so the component renders
    and can read / write browser cookies on every Streamlit rerun."""
    return stx.CookieManager()
