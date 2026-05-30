from viale_manager.admin.widgets import reservations_widget_context


def dashboard_callback(request, context):
    context.update(reservations_widget_context(request))
    return context