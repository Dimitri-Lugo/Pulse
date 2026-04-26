import extra_streamlit_components as stx


# Runs every time the page reruns so the app can read and write browser cookies
def get_cookie_manager():
    return stx.CookieManager()
