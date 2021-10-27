from django.conf import settings
from django.conf.locale.en import formats as formats_us
from django.conf.locale.en_GB import formats as formats_gb

# Override the regular locale settings to support 24 hour time.
if settings.USE_24_HOUR_TIME_FORMAT:
    DATETIME_FORMAT = 'N j, Y, H:i:s'
    CUSTOM_INPUT_FORMATS = [
        '%m/%d/%Y %H:%M:%S',    # '10/25/2006 14:30:59'
        '%m/%d/%Y %H:%M',       # '10/25/2006 14:30'
    ]
    SHORT_DATETIME_FORMAT = 'm/d/Y G:i:s'
    TIME_FORMAT = 'H:i:s'
else:
    # These formats are added to support the locale style of Baby Buddy's
    # frontend library, which uses momentjs.
    CUSTOM_INPUT_FORMATS = [
        '%m/%d/%Y %I:%M:%S %p',  # '10/25/2006 2:30:59 PM'
        '%m/%d/%Y %I:%M %p',     # '10/25/2006 2:30 PM'
    ]

# Add custom "short" version of `MONTH_DAY_FORMAT`. This customization will
# only work with the locale format locale specified by this file.
SHORT_MONTH_DAY_FORMAT = 'M j'

# Combine en_US (en) and en_GB formats. This seems to be necessary because when
# an en language variation is used this file is still loaded and there is no
# way to implement e.g. an en_US format. Combining these formats allows the app
# to support both en (en_US) and en_GB without enforcing US-centric input
# formats on users with a en_GB setting.
formats = formats_us.DATETIME_INPUT_FORMATS + formats_gb.DATETIME_INPUT_FORMATS

# Append all other input formats from the base locale.
DATETIME_INPUT_FORMATS = CUSTOM_INPUT_FORMATS + formats
