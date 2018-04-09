from validate import VdtParamError
from validate import VdtTypeError
from validate import VdtValueTooLongError
from validate import VdtValueTooShortError
from validate import VdtValueError
from validate import VdtValueTooSmallError
from validate import VdtValueTooBigError
from validate import Validator
from email.utils import parseaddr


def yes_no(value):
    testValue = value.strip().upper()
    if testValue not in ('Y', 'N'):
        raise VdtValueError(value)
    return testValue == 'Y'


def email(value):
    if not value:
        return ""
    result = parseaddr(value)
    if not result[1]:
        raise VdtValueError
    return "%s <%s>" % (result[0], result[1])


def email_list(value):
    if not value:
        value = []
    elif isinstance(value, str):
        value = [value]
    newList = []
    for address in value:
        result = parseaddr(address)
        if not result[1]:
            raise VdtValueError
        newList.append(("%s <%s>" % (result[0], result[1])).strip())
    return newList


def option_list(value, options=None, min=None, max=None):
    if options and not isinstance(options, list):
        raise VdtParamError('options', options)

    if min is not None:
        try:
            min = int(min)
        except ValueError:
            raise VdtParamError('min', min)

    if max is not None:
        try:
            max = int(max)
        except ValueError:
            raise VdtParamError('max', max)

    if min < 0:
        raise VdtParamError('min', min)

    if max < min:
        raise VdtParamError('max', max)

    if isinstance(value, str):
        strVal = value.strip()
        value = []
        if strVal:
            value = [strVal]

    if not isinstance(value, list):
        raise VdtTypeError(value)

    if max and len(value) > max:
        raise VdtValueTooLongError(value)
    elif min and len(value) < min:
        raise VdtValueTooShortError(value)

    if not options:
        return value

    for entry in value:
        if entry not in options:
            raise VdtValueError(value)

    return value


def limit_option(value, min=0, max=None, warn_default=0, alert_default=0):
    valid_options = ['WARN', 'ALERT']

    # Check min/max parameters
    if min is not None:
        try:
            min = int(min)
        except ValueError:
            raise VdtParamError('min', min)
    if max is not None:
        try:
            max = int(max)
        except ValueError:
            raise VdtParamError('max', max)

    # Check value is a list
    if not isinstance(value, list):
        raise VdtTypeError(value)

    # Check for too many or too few values
    if len(value) > len(valid_options):
        raise VdtValueTooLongError(value)
    # elif len(value) < 1:
    #     raise VdtValueTooShortError(value)
    returnDict = {'WARN': warn_default, 'ALERT': alert_default}
    valueDict = {}
    for entry in value:
        # Check list value is a string
        try:
            entry = str(entry)
        except ValueError:
            raise VdtValueError(entry)

        optionParts = entry.split(':', 1)

        limitType = optionParts[0].strip().upper()
        limitVal = optionParts[1]

        if limitType not in valid_options:
            raise VdtValueError(limitType)
        try:
            limitVal = int(limitVal)
        except ValueError:
            raise VdtTypeError(limitVal)

        # Check limits values fall in range
        if max is not None and limitVal > max:
            raise VdtValueTooBigError(limitVal)
        elif min is not None and limitVal < min:
            raise VdtValueTooSmallError(limitVal)

        # Check duplicate
        if limitType in valueDict:
            raise VdtValueError(value)
        valueDict[limitType] = limitVal

    returnDict.update(valueDict)
    # print returnDict
    return ','.join(['%s: %s' % (key, value) for (key, value) in returnDict.items()])


def sample_option(value, samples_default=1, interval_default=1):

    valid_options = ['SAMPLES', 'INTERVAL']

    # Check samples_default and interval_default parameters
    try:
        samples_default = int(samples_default)
    except ValueError:
        raise VdtParamError('samples_default', samples_default)
    if samples_default < 1:
        raise VdtParamError('samples_default', samples_default)
    try:
        interval_default = int(interval_default)
    except ValueError:
        raise VdtParamError('interval_default', interval_default)
    if interval_default < 1:
        raise VdtParamError('interval_default', interval_default)

    returnDict = {'SAMPLES': samples_default, 'INTERVAL': interval_default}

    if value and not isinstance(value, list):
        raise VdtTypeError(value)

    if value is None or len(value) == 0:
        return returnDict

    if len(value) > len(valid_options):
        raise VdtValueTooLongError(value)

    updateDict = {}
    for entry in value:
        try:
            entry = str(entry)
        except ValueError:
            raise VdtValueError(entry)

        optionParts = entry.split(':', 1)
        if len(optionParts) != 2:
            raise VdtValueError(entry)

        limitType = optionParts[0].strip().upper()
        limitVal = optionParts[1]

        if limitType not in valid_options:
            raise VdtValueError(limitType)
        try:
            limitVal = int(limitVal)
        except ValueError:
            raise VdtTypeError(limitVal)

        if limitVal < 1:
            raise VdtValueTooSmallError(limitVal)

        if limitType in updateDict:
            raise VdtValueError(value)

        updateDict[limitType] = limitVal

    returnDict.update(updateDict)
    return ','.join(['%s: %s' % (key, value) for (key, value) in returnDict.items()])


def force_string_list(value, min=None, max=None):
    if value is None:
        value = []
    elif isinstance(value, str):
        value = [value.strip()]
    return Validator().functions['string_list'](value, min, max)


def force_int_list(value, min=None, max=None):
    if value is None:
        value = []
    elif isinstance(value, str):
        value = value.strip()
        if value:
            value = [value]
        else:
            value = []
    return Validator().functions['int_list'](value, min, max)
