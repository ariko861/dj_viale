class DBRouter:
    app_label = 'viale_manager'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'viale_manager'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'viale_manager'
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label == self.app_label:
            return db == 'viale_manager'
        return db == 'default'