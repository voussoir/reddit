MailForwarding
========

Forward all comments and Private Messages from one account to another. This bot will store it's unsent mail in an sql file so you will not miss out on messages due to any downtime.

If the inboxed item was a comment, the forward will include it's permalink. If it was a PM, the forward will include a link to compose a new message with a preset "re: " subjectline. The forward will also include the timestamp of the original message in UTC.

Subjectlines are limited to 100 chars; body text 10,000. If they are too long, the excess will be silently sliced off. It's a real edge-case for this to be an issue.

This was done on a whim. Please notify me of bugs.