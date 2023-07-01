from benji.notification.telegram.telegram_notify import TelegramNotify


def alert_failed_to_create_version_when_full_storage(config, version):
    message = "`Failed to create version_id {}:" \
              "\nReason: Full storage {}" \
              "\nVolume_id: {}" \
              "\nUser: {}" \
              "\nEmail: {}" \
              "\nCreated at: {}`".format(version.id, version.storage.configuration['path'],
                                         version.volume, version.storage.user.user_name,
                                         version.storage.user.email, version.created_at)
    telegram_notify = TelegramNotify(config)
    telegram_notify.send_message(message)

