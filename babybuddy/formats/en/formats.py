# This files adds two new date input formats to support Baby Buddy's frontend
# library formats:
#   - %m/%d/%Y %I:%M:%S %p
#   - %m/%d/%Y %I:%M %p
#
# The remaining formats come from the base Django formats.
#
# See django.cong.locale.en.
DATETIME_INPUT_FORMATS = [
    '%m/%d/%Y %I:%M:%S %p',  # '10/25/2006 2:30:59 PM' (new)
    '%m/%d/%Y %I:%M %p',     # '10/25/2006 2:30 PM' (new)
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M:%S.%f',  # '2006-10-25 14:30:59.000200'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M:%S.%f',  # '10/25/2006 14:30:59.000200'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M:%S.%f',  # '10/25/06 14:30:59.000200'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
]
