# CNM Notifier

This project provides simple notification support for networks being offline via
the Church Network Manager for the Church of Jesus Christ of Latter-day Saints.

## Configuration

The following values need to be configured via environment variables or docker
compose secrets:

- SMTP_HOST - SMTP server host
- SMTP_PORT - SMTP server port
- SMTP_USERNAME - SMTP server username
- SMTP_PASSWORD - SMTP server password
- MAIL_SENDER -  "from" address for notifications
- MAIL_RECIPIENTS - list of mail recipients, comma-separated
- CNM_USERNAME - User name to log in to CNM
- CNM_PASSWORD - Password to log in to CNM
- CNM_FIREWALLS - list of firewall IDs, comma-separated
