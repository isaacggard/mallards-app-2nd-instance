import app
from pages.fan_master_filters import install_fan_master_filters


install_fan_master_filters(app)
app.initialize_session_state()
app.render_dashboard_page()
