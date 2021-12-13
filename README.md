# Air-ticket-price-parser
Parser for air tickets' price

# How to
- Install Firefox
    - If geckodriver.exe is not compatible with your Firefox version, download the compatible version from https://github.com/mozilla/geckodriver/releases and replace it

- At email_client.py
    - Replace `user_name` and `user_pass` with your own email account's address and password (or secret for third party log in)
    - Replace `SMTP_address` to match with your email service provider

- At parser.py
    - Replace `fromCity` and `toCity` as you need
    - Replace `fromDates` and `toDates`
        - Query will be made on 
        ```python
        (dateGo, dateBack) for dateBack in toDates for dateGo in fromDates
        ```
    - Set `notification_threshold` to the expected price value you want to be notified
- Set filter
    - Currently `not transfer` for Go, `not transfer and arrival time between 07:00 and 17:00` for Back