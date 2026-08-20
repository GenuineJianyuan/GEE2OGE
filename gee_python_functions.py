"""
GEE API 的 Python 等价实现模块。

本模块实现了 GEE (Google Earth Engine) API 中映射为 Python 原生实现的功能，
包括日期处理、字典操作、列表操作、数值运算、字符串格式化和循环操作等。

每个函数都对应 GEE 中的一个 API，并提供了纯 Python 的等价实现。
"""

import math
import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union


# ============================================================
# print - 控制台输出
# ============================================================

def gee_print(*args, **kwargs) -> None:
    """对应 GEE 的 print() 函数，输出到控制台

    GEE 描述: Outputs a specified value or object to the console for debugging.
              将指定的值或对象输出到控制台，用于调试和查看中间结果。

    Args:
        *args: 要输出的值
        **kwargs: 传递给 Python print 的其他参数

    Returns:
        None
    """
    print(*args, **kwargs)


# ============================================================
# ee.Array -> Python List / 矩阵运算
# ============================================================

def ee_array(values, pixel_type=None):
    """对应 GEE 的 ee.Array() 构造函数

    GEE 描述: 返回具有给定坐标值的数组。values 参数可以是现有数组、数字、
             数字列表或嵌套数字列表。pixelType 参数指定数组中每个数字的类型。

    Args:
        values: 数字、数字列表或嵌套数字列表
        pixel_type: 像素类型（纯 Python 实现中仅用于类型转换）

    Returns:
        list: Python 列表（一维或二维）

    Example:
        >>> ee_array([1, 2, 3])
        [1, 2, 3]
        >>> ee_array([[1, 2], [3, 4]])
        [[1, 2], [3, 4]]
    """
    if pixel_type is not None:
        type_map = {
            'int': int, 'long': int, 'float': float,
            'double': float, 'byte': int, 'short': int,
            'int8': int, 'int16': int, 'int32': int,
            'int64': int, 'uint8': int, 'uint16': int,
            'uint32': int, 'uint64': int
        }
        py_type = type_map.get(str(pixel_type).lower(), float)
        if isinstance(values, list):
            return [py_type(v) if not isinstance(v, list) else [py_type(x) for x in v] for v in values]
        return py_type(values)
    return values


def ee_array_matrix_determinant(matrix):
    """对应 GEE 的 ee.Array.matrixDeterminant()，计算矩阵行列式

    GEE 描述: 计算矩阵的行列式。

    Args:
        matrix: 二维列表表示的方阵

    Returns:
        float: 行列式的值

    Raises:
        ValueError: 如果矩阵不是方阵

    Example:
        >>> ee_array_matrix_determinant([[1, 2], [3, 4]])
        -2.0
    """
    n = len(matrix)
    if not all(len(row) == n for row in matrix):
        raise ValueError("矩阵必须是方阵")
    if n == 1:
        return float(matrix[0][0])
    if n == 2:
        return float(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0])
    # 通用情况：使用 LU 分解
    m = [row[:] for row in matrix]
    det = 1.0
    for i in range(n):
        pivot = i
        for j in range(i + 1, n):
            if abs(m[j][i]) > abs(m[pivot][i]):
                pivot = j
        if pivot != i:
            m[i], m[pivot] = m[pivot], m[i]
            det *= -1
        if m[i][i] == 0:
            return 0.0
        det *= m[i][i]
        for j in range(i + 1, n):
            factor = m[j][i] / m[i][i]
            for k in range(i, n):
                m[j][k] -= factor * m[i][k]
    return det


def ee_array_matrix_inverse(matrix):
    """对应 GEE 的 ee.Array.matrixInverse()，计算矩阵逆

    GEE 描述: 计算矩阵的逆。

    Args:
        matrix: 二维列表表示的方阵

    Returns:
        list: 逆矩阵（二维列表）

    Raises:
        ValueError: 如果矩阵不可逆

    Example:
        >>> inv = ee_array_matrix_inverse([[4, 7], [2, 6]])
        >>> inv  # [[0.6, -0.7], [-0.2, 0.4]]
    """
    n = len(matrix)
    if not all(len(row) == n for row in matrix):
        raise ValueError("矩阵必须是方阵")

    # 构造增广矩阵 [A | I]
    augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]

    for i in range(n):
        # 选主元
        pivot = i
        for j in range(i + 1, n):
            if abs(augmented[j][i]) > abs(augmented[pivot][i]):
                pivot = j
        if pivot != i:
            augmented[i], augmented[pivot] = augmented[pivot], augmented[i]

        if augmented[i][i] == 0:
            raise ValueError("矩阵不可逆：奇异矩阵")

        # 缩放当前行
        factor = augmented[i][i]
        for j in range(2 * n):
            augmented[i][j] /= factor

        # 消元
        for j in range(n):
            if j != i:
                factor = augmented[j][i]
                for k in range(2 * n):
                    augmented[j][k] -= factor * augmented[i][k]

    # 提取逆矩阵（右半部分）
    return [row[n:] for row in augmented]


def ee_array_matrix_trace(matrix):
    """对应 GEE 的 ee.Array.matrixTrace()，计算矩阵迹

    GEE 描述: 计算矩阵的迹（对角线元素之和）。

    Args:
        matrix: 二维列表表示的方阵

    Returns:
        float: 迹的值

    Example:
        >>> ee_array_matrix_trace([[1, 2], [3, 4]])
        5
    """
    return float(sum(matrix[i][i] for i in range(len(matrix))))


# ============================================================
# ee.Date / ee.DateRange -> Python Function
# ============================================================

# GEE 支持的时间单位及对应的秒数
_DATE_UNITS = {
    'second': 1,
    'minute': 60,
    'hour': 3600,
    'day': 86400,
    'week': 604800,
    'month': 2592000,  # 近似 30 天
    'year': 31536000,  # 近似 365 天
}


def _parse_gee_date(date_input, tz=None):
    """将 GEE 的日期输入转换为 Python datetime 对象

    Args:
        date_input: 日期输入，可以是:
                   - int/float: 毫秒时间戳
                   - str: ISO 格式日期字符串 (如 '2023-01-01', '2023-01-01T08:00:00')
                   - datetime: Python datetime 对象
        tz: 时区字符串（纯 Python 中使用 UTC 或本地时区）

    Returns:
        datetime: Python datetime 对象（UTC）
    """
    if isinstance(date_input, datetime):
        if date_input.tzinfo is None:
            return date_input.replace(tzinfo=timezone.utc)
        return date_input

    if isinstance(date_input, (int, float)):
        return datetime.fromtimestamp(date_input / 1000.0, tz=timezone.utc)

    if isinstance(date_input, str):
        # 尝试多种格式解析
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_input, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        # 如果都不匹配，尝试用 dateutil 或 isoformat
        try:
            dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass

    raise ValueError(f"无法解析日期: {date_input}")


def ee_date(date_input, tz=None):
    """对应 GEE 的 ee.Date() 构造函数

    GEE 描述: 创建新的 Date 对象。接受数字（毫秒时间戳）、ISO 日期字符串、
             JavaScript Date 或 ComputedObject 等多种输入类型。

    Args:
        date_input: 日期输入（毫秒时间戳、ISO 字符串、datetime 对象等）
        tz: 时区字符串（可选）

    Returns:
        datetime: Python datetime 对象（UTC 时区）

    Example:
        >>> ee_date('2023-01-01')
        datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        >>> ee_date(1672531200000)  # 毫秒时间戳
        datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    """
    return _parse_gee_date(date_input, tz)


def ee_date_advance(date, delta, unit, time_zone=None):
    """对应 GEE 的 ee.Date.advance()，在日期上增加指定时间

    GEE 描述: 通过在给定日期上添加指定的 delta 和 unit 来创建新日期。
             unit 可以是 'year', 'month', 'week', 'day', 'hour', 'minute', 'second'。

    Args:
        date: 基准日期（可以是 datetime、字符串或时间戳）
        delta: 要增加的数量（正数或负数）
        unit: 时间单位 ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
        time_zone: 时区（可选，暂未使用）

    Returns:
        datetime: 增加后的新日期

    Raises:
        ValueError: 如果单位不支持

    Example:
        >>> dt = ee_date('2023-01-15')
        >>> ee_date_advance(dt, 5, 'day')
        datetime.datetime(2023, 1, 20, 0, 0, tzinfo=...)
        >>> ee_date_advance(dt, -1, 'month')
        datetime.datetime(2022, 12, 15, 0, 0, tzinfo=...)
    """
    dt = _parse_gee_date(date)

    if unit == 'year':
        new_year = dt.year + int(delta)
        # 处理闰年 2 月 29 日的情况
        day = min(dt.day, _days_in_month(new_year, dt.month))
        return dt.replace(year=new_year, day=day)

    elif unit == 'month':
        total_months = dt.year * 12 + (dt.month - 1) + int(delta)
        new_year = total_months // 12
        new_month = total_months % 12 + 1
        day = min(dt.day, _days_in_month(new_year, new_month))
        return dt.replace(year=new_year, month=new_month, day=day)

    elif unit in _DATE_UNITS:
        seconds = int(delta * _DATE_UNITS[unit])
        return dt + timedelta(seconds=seconds)

    else:
        raise ValueError(f"不支持的时间单位: {unit}")


def _days_in_month(year, month):
    """计算指定年月的天数

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        int: 该月的天数
    """
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return last_day


def ee_date_day_of_year(date):
    """对应 GEE 的 ee.Date.dayOfYear()，获取一年中的第几天

    GEE 描述: 返回日期在一年中的第几天（1-366）。

    Args:
        date: 日期输入

    Returns:
        int: 一年中的第几天（1-366）

    Example:
        >>> ee_date_day_of_year('2023-01-01')
        1
        >>> ee_date_day_of_year('2023-12-31')
        365
    """
    dt = _parse_gee_date(date)
    return dt.timetuple().tm_yday


def ee_date_difference(date, start, unit):
    """对应 GEE 的 ee.Date.difference()，计算两个日期的差值

    GEE 描述: 计算两个日期之间的差值，返回浮点数。单位可以是
             'year', 'month', 'week', 'day', 'hour', 'minute', 'second'。

    Args:
        date: 结束日期
        start: 开始日期
        unit: 差值单位

    Returns:
        float: 两个日期之间的差值（以指定单位计）

    Example:
        >>> ee_date_difference('2023-01-15', '2023-01-01', 'day')
        14.0
        >>> ee_date_difference('2023-01-01', '2022-01-01', 'year')
        1.0
    """
    end_dt = _parse_gee_date(date)
    start_dt = _parse_gee_date(start)
    delta_seconds = (end_dt - start_dt).total_seconds()

    if unit == 'year':
        # 精确计算年差
        years = end_dt.year - start_dt.year
        if (end_dt.month, end_dt.day) < (start_dt.month, start_dt.day):
            years -= 1
        remaining_days = (end_dt - start_dt.replace(
            year=end_dt.year if years >= 0 else end_dt.year + 1
        )).days
        return float(years) + remaining_days / 365.0
    elif unit == 'month':
        return delta_seconds / _DATE_UNITS['month']
    elif unit in _DATE_UNITS:
        return delta_seconds / _DATE_UNITS[unit]
    else:
        raise ValueError(f"不支持的时间单位: {unit}")


def ee_date_format(date, fmt=None, time_zone=None):
    """对应 GEE 的 ee.Date.format()，将日期格式化为字符串

    GEE 描述: 将日期转换为字符串。格式模式遵循 Joda-Time DateTimeFormat 规范。
             如果不提供格式，将使用 ISO 标准日期格式。

    Args:
        date: 日期输入
        fmt: 格式字符串（使用 Python strftime 格式），None 则使用 ISO 格式
        time_zone: 时区（可选）

    Returns:
        str: 格式化后的日期字符串

    Example:
        >>> ee_date_format('2023-01-15', '%Y-%m-%d')
        '2023-01-15'
        >>> ee_date_format('2023-01-15T08:30:00', '%Y/%m/%d %H:%M')
        '2023/01/15 08:30'
    """
    dt = _parse_gee_date(date)
    if fmt is None:
        # 默认 ISO 格式
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    return dt.strftime(fmt)


def ee_date_get(date, unit, time_zone=None):
    """对应 GEE 的 ee.Date.get()，获取日期的指定时间单位值

    GEE 描述: 返回日期的指定单位值。unit 可以是 'year', 'month', 'week',
             'day', 'hour', 'minute', 'second'。

    Args:
        date: 日期输入
        unit: 时间单位

    Returns:
        int: 对应的时间单位值

    Example:
        >>> ee_date_get('2023-01-15', 'year')
        2023
        >>> ee_date_get('2023-01-15', 'month')
        1
        >>> ee_date_get('2023-01-15', 'day')
        15
    """
    dt = _parse_gee_date(date)
    unit_map = {
        'year': lambda d: d.year,
        'month': lambda d: d.month,
        'week': lambda d: d.isocalendar()[1],
        'day': lambda d: d.day,
        'hour': lambda d: d.hour,
        'minute': lambda d: d.minute,
        'second': lambda d: d.second,
    }
    if unit not in unit_map:
        raise ValueError(f"不支持的时间单位: {unit}")
    return unit_map[unit](dt)


def ee_date_get_relative(date, unit, in_unit, time_zone=None):
    """对应 GEE 的 ee.Date.getRelative()，获取相对于较大单位的0基单位值

    GEE 描述: 返回日期相对于较大单位的 0 基单位值。例如，
             getRelative('day', 'month') 返回日期在月份中的天数（0-基）。

    Args:
        date: 日期输入
        unit: 要获取的单位 ('month', 'week', 'day', 'hour', 'minute', 'second')
        in_unit: 参考的较大单位 ('year', 'month', 'week', 'day', 'hour', 'minute')
        time_zone: 时区（可选）

    Returns:
        int: 0-基的相对单位值

    Example:
        >>> ee_date_get_relative('2023-01-15', 'day', 'month')
        14  # 0-基，即第15天 = 14
    """
    dt = _parse_gee_date(date)
    value = ee_date_get(date, unit, time_zone)
    if unit == 'day':
        return value - 1
    elif unit == 'month':
        return value - 1
    elif unit == 'week':
        return value - 1
    return value


def ee_date_parse(fmt, date_string, time_zone=None):
    """对应 GEE 的 ee.Date.parse()，解析日期字符串为 Date 对象

    GEE 描述: 根据给定格式将日期字符串转换为 Date 对象。格式模式遵循
             Joda-Time DateTimeFormat 规范。

    Args:
        fmt: 日期格式字符串（Python strftime 格式）
        date_string: 要解析的日期字符串
        time_zone: 时区（可选）

    Returns:
        datetime: 解析后的 datetime 对象

    Example:
        >>> ee_date_parse('%Y-%m-%d', '2023-01-15')
        datetime.datetime(2023, 1, 15, 0, 0, tzinfo=...)
    """
    dt = datetime.strptime(date_string, fmt)
    return dt.replace(tzinfo=timezone.utc)


def ee_date_subtract(date, delta, unit, time_zone=None):
    """对应 GEE 的 ee.Date.subtract()，从日期上减去指定时间

    GEE 描述: 从日期中减去指定的 delta 和 unit，创建新日期。

    Args:
        date: 基准日期
        delta: 要减去的数量
        unit: 时间单位

    Returns:
        datetime: 减去后的新日期

    Example:
        >>> ee_date_subtract('2023-01-15', 5, 'day')
        datetime.datetime(2023, 1, 10, 0, 0, tzinfo=...)
    """
    return ee_date_advance(date, -delta, unit, time_zone)


def ee_date_range(start, end=None, time_zone=None):
    """对应 GEE 的 ee.DateRange() 构造函数

    GEE 描述: 创建一个 DateRange，由开始（包含）和结束（排除）日期组成。
             如果未提供结束日期，则创建从开始日期起 1 毫秒的范围。

    Args:
        start: 开始日期（包含）
        end: 结束日期（排除），可选
        time_zone: 时区（可选）

    Returns:
        dict: 表示日期范围的字典，包含 start 和 end

    Example:
        >>> ee_date_range('2023-01-01', '2023-12-31')
        {'start': datetime(...), 'end': datetime(...)}
    """
    start_dt = _parse_gee_date(start)
    if end is not None:
        end_dt = _parse_gee_date(end)
    else:
        end_dt = start_dt + timedelta(milliseconds=1)
    return {'start': start_dt, 'end': end_dt}


# ============================================================
# ee.Dictionary -> Python Dictionary
# ============================================================

def ee_dictionary(dict_data=None):
    """对应 GEE 的 ee.Dictionary() 构造函数

    GEE 描述: 创建新的 Dictionary。接受字典、键值对列表或空参数。

    Args:
        dict_data: 字典、键值对列表或 None

    Returns:
        dict: Python 字典

    Example:
        >>> ee_dictionary({'key': 'value'})
        {'key': 'value'}
        >>> ee_dictionary([['a', 1], ['b', 2]])
        {'a': 1, 'b': 2}
        >>> ee_dictionary()
        {}
    """
    if dict_data is None:
        return {}
    if isinstance(dict_data, dict):
        return copy.deepcopy(dict_data)
    if isinstance(dict_data, list):
        if len(dict_data) > 0 and isinstance(dict_data[0], (list, tuple)) and len(dict_data[0]) == 2:
            return dict(dict_data)
        raise ValueError("列表必须是键值对列表，如 [['key', 'value'], ...]")
    raise TypeError(f"不支持的类型: {type(dict_data)}")


def ee_dictionary_get(dictionary, key, default_value=None):
    """对应 GEE 的 ee.Dictionary.get()，从字典中获取值

    GEE 描述: 从字典中提取命名值。如果指定的键未找到，返回默认值。

    Args:
        dictionary: Python 字典
        key: 键名
        default_value: 默认值（键不存在时返回）

    Returns:
        对应的值，如果键不存在返回 default_value

    Example:
        >>> d = {'name': 'test', 'value': 42}
        >>> ee_dictionary_get(d, 'name')
        'test'
        >>> ee_dictionary_get(d, 'missing', 'default')
        'default'
    """
    return dictionary.get(key, default_value)


def ee_dictionary_get_info(dictionary, callback=None):
    """对应 GEE 的 ee.Dictionary.getInfo()，获取字典信息

    GEE 描述: 从服务器检索对象的值。在纯 Python 实现中直接返回字典副本。

    Args:
        dictionary: Python 字典
        callback: 回调函数（可选，异步模式用）

    Returns:
        dict: 字典的深拷贝

    Example:
        >>> d = {'key': 'value'}
        >>> result = ee_dictionary_get_info(d)
        >>> result is d
        False
    """
    result = copy.deepcopy(dictionary)
    if callback:
        return callback(result)
    return result


def ee_dictionary_set(dictionary, key, value):
    """对应 GEE 的 ee.Dictionary.set()，设置字典中的值

    GEE 描述: 在字典中设置值，返回修改后的字典。

    Args:
        dictionary: Python 字典
        key: 键名
        value: 要设置的值

    Returns:
        dict: 修改后的字典（返回副本以保持函数式风格）

    Example:
        >>> d = {'a': 1}
        >>> ee_dictionary_set(d, 'b', 2)
        {'a': 1, 'b': 2}
    """
    new_dict = copy.deepcopy(dictionary)
    new_dict[key] = value
    return new_dict


def ee_dictionary_to_list(dictionary):
    """对应 GEE 的 ee.Dictionary.toList()，将字典转换为列表

    GEE 描述: 将字典转换为键值对列表。

    Args:
        dictionary: Python 字典

    Returns:
        list: 键值对列表 [[key, value], ...]

    Example:
        >>> ee_dictionary_to_list({'a': 1, 'b': 2})
        [['a', 1], ['b', 2]]
    """
    return [[k, v] for k, v in dictionary.items()]


# ============================================================
# ee.Number -> Python Int / Float
# ============================================================

def ee_number(number):
    """对应 GEE 的 ee.Number() 构造函数

    GEE 描述: 创建一个 Number 对象。

    Args:
        number: 数字或可转换为数字的值

    Returns:
        int 或 float: Python 数值类型

    Example:
        >>> ee_number(42)
        42
        >>> ee_number(3.14)
        3.14
        >>> ee_number('123')
        123
    """
    if isinstance(number, (int, float)):
        return number
    if isinstance(number, str):
        if '.' in number or 'e' in number.lower():
            return float(number)
        return int(number)
    return float(number)


def ee_number_divide(left, right):
    """对应 GEE 的 ee.Number.divide()，除法运算

    GEE 描述: 计算两个数的除法。

    Args:
        left: 被除数
        right: 除数

    Returns:
        float: 除法结果

    Example:
        >>> ee_number_divide(10, 3)
        3.3333333333333335
    """
    return float(left) / float(right)


def ee_number_format(number, pattern=None):
    """对应 GEE 的 ee.Number.format()，格式化数字为字符串

    GEE 描述: 按照指定格式将数字格式化为字符串。

    Args:
        number: 数字
        pattern: 格式模式（如 '%.2f'、'%d' 等）

    Returns:
        str: 格式化后的字符串

    Example:
        >>> ee_number_format(3.14159, '%.2f')
        '3.14'
        >>> ee_number_format(1234567, '%,d')
        '1,234,567'
    """
    if pattern:
        if '%' in pattern:
            return pattern % number
        return format(number, pattern)
    return str(number)


def ee_number_gte(left, right):
    """对应 GEE 的 ee.Number.gte()，大于等于判断

    GEE 描述: 判断左值是否大于等于右值。

    Args:
        left: 左操作数
        right: 右操作数

    Returns:
        bool: left >= right

    Example:
        >>> ee_number_gte(5, 3)
        True
        >>> ee_number_gte(3, 5)
        False
    """
    return left >= right


def ee_number_lte(left, right):
    """对应 GEE 的 ee.Number.lte()，小于等于判断

    GEE 描述: 判断左值是否小于等于右值。

    Args:
        left: 左操作数
        right: 右操作数

    Returns:
        bool: left <= right

    Example:
        >>> ee_number_lte(3, 5)
        True
        >>> ee_number_lte(5, 3)
        False
    """
    return left <= right


def ee_number_multiply(left, right):
    """对应 GEE 的 ee.Number.multiply()，乘法运算

    GEE 描述: 计算两个数的乘积。

    Args:
        left: 左乘数
        right: 右乘数

    Returns:
        int 或 float: 乘积

    Example:
        >>> ee_number_multiply(6, 7)
        42
    """
    result = left * right
    return result


# ============================================================
# ee.String -> Python String
# ============================================================

def ee_string(string_value):
    """对应 GEE 的 ee.String() 构造函数

    GEE 描述: 创建一个 String 对象。

    Args:
        string_value: 字符串或可转换为字符串的值

    Returns:
        str: Python 字符串

    Example:
        >>> ee_string('hello')
        'hello'
        >>> ee_string(123)
        '123'
    """
    return str(string_value)


def ee_string_format(template, *args, **kwargs):
    """对应 GEE 的 ee.String.format()，格式化字符串

    GEE 描述: 按照指定格式创建格式化字符串。在 GEE 中通常以
             ee.String('Hello {name}').format(name='World') 方式调用。

    Args:
        template: 基础字符串模板（包含 {placeholder} 占位符）
        *args: 位置参数（按顺序填充占位符）
        **kwargs: 关键字参数（按名称填充占位符）

    Returns:
        str: 格式化后的字符串

    Example:
        >>> ee_string_format('Hello {name}!', name='World')
        'Hello World!'
        >>> ee_string_format('{} + {} = {}', 1, 2, 3)
        '1 + 2 = 3'
    """
    if args or kwargs:
        return template.format(*args, **kwargs)
    return template


# ============================================================
# ee.List -> Python List
# ============================================================

def ee_list(list_data=None):
    """对应 GEE 的 ee.List() 构造函数

    GEE 描述: 从列表或可迭代对象构造新的 List。

    Args:
        list_data: 列表、可迭代对象或 None

    Returns:
        list: Python 列表

    Example:
        >>> ee_list([1, 2, 3])
        [1, 2, 3]
        >>> ee_list()
        []
    """
    if list_data is None:
        return []
    return list(list_data)


def ee_list_contains(lst, element):
    """对应 GEE 的 ee.List.contains()，判断列表是否包含元素

    GEE 描述: 如果列表包含元素则返回 True。

    Args:
        lst: 列表
        element: 要检查的元素

    Returns:
        bool: 是否包含

    Example:
        >>> ee_list_contains([1, 2, 3], 2)
        True
        >>> ee_list_contains([1, 2, 3], 4)
        False
    """
    return element in lst


def ee_list_filter(lst, filter_fn):
    """对应 GEE 的 ee.List.filter()，按条件过滤列表

    GEE 描述: 根据给定的过滤条件筛选列表。

    Args:
        lst: 列表
        filter_fn: 过滤函数（返回 True 保留元素）

    Returns:
        list: 过滤后的列表

    Example:
        >>> ee_list_filter([1, 2, 3, 4], lambda x: x > 2)
        [3, 4]
    """
    return [item for item in lst if filter_fn(item)]


def ee_list_flatten(lst):
    """对应 GEE 的 ee.List.flatten()，将嵌套列表展平

    GEE 描述: 将所有子列表展平为单个列表。

    Args:
        lst: 嵌套列表

    Returns:
        list: 展平后的列表

    Example:
        >>> ee_list_flatten([[1, 2], [3, [4, 5]]])
        [1, 2, 3, 4, 5]
    """
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(ee_list_flatten(item))
        else:
            result.append(item)
    return result


def ee_list_get(lst, index):
    """对应 GEE 的 ee.List.get()，获取列表指定位置的元素

    GEE 描述: 获取列表指定位置的元素。支持负索引。

    Args:
        lst: 列表
        index: 索引（支持负数）

    Returns:
        指定位置的元素

    Example:
        >>> ee_list_get([10, 20, 30], 1)
        20
        >>> ee_list_get([10, 20, 30], -1)
        30
    """
    return lst[index]


def ee_list_group(lst):
    """对应 GEE 的 ee.List.group()，对列表元素进行分组

    GEE 描述: 将列表元素按相等分组，返回 [[element, count], ...] 格式。

    Args:
        lst: 列表

    Returns:
        list: 分组结果 [[element, count], ...]

    Example:
        >>> ee_list_group(['a', 'b', 'a', 'c', 'b', 'a'])
        [['a', 3], ['b', 2], ['c', 1]]
    """
    seen = {}
    for item in lst:
        if item in seen:
            seen[item] += 1
        else:
            seen[item] = 1
    return [[k, v] for k, v in seen.items()]


def ee_list_join(lst, separator=''):
    """对应 GEE 的 ee.List.join()，用分隔符连接列表元素

    GEE 描述: 返回由列表元素用指定分隔符连接而成的字符串。

    Args:
        lst: 列表
        separator: 分隔符（默认为空字符串）

    Returns:
        str: 连接后的字符串

    Example:
        >>> ee_list_join(['a', 'b', 'c'], '-')
        'a-b-c'
        >>> ee_list_join([1, 2, 3], ', ')
        '1, 2, 3'
    """
    return separator.join(str(item) for item in lst)


def ee_list_map(lst, algorithm, drop_nulls=False):
    """对应 GEE 的 ee.List.map()，对列表每个元素应用函数

    GEE 描述: 在列表上映射算法，返回结果列表。

    Args:
        lst: 列表
        algorithm: 映射函数
        drop_nulls: 是否丢弃 None 值

    Returns:
        list: 映射结果列表

    Example:
        >>> ee_list_map([1, 2, 3], lambda x: x * 2)
        [2, 4, 6]
        >>> ee_list_map([1, 2, None, 3], lambda x: x, drop_nulls=True)
        [1, 2, 3]
    """
    result = [algorithm(item) for item in lst]
    if drop_nulls:
        result = [item for item in result if item is not None]
    return result


def ee_list_remove(lst, element):
    """对应 GEE 的 ee.List.remove()，移除第一个匹配元素

    GEE 描述: 从列表中移除第一个匹配的元素。

    Args:
        lst: 列表
        element: 要移除的元素

    Returns:
        list: 移除后的新列表

    Example:
        >>> ee_list_remove([1, 2, 3, 2], 2)
        [1, 3, 2]
    """
    new_list = list(lst)
    try:
        new_list.remove(element)
    except ValueError:
        pass
    return new_list


def ee_list_repeat(value, count):
    """对应 GEE 的 ee.List.repeat()，重复值创建列表

    GEE 描述: 返回包含重复值的新列表。

    Args:
        value: 要重复的值
        count: 重复次数

    Returns:
        list: 重复值组成的列表

    Example:
        >>> ee_list_repeat(0, 5)
        [0, 0, 0, 0, 0]
        >>> ee_list_repeat('x', 3)
        ['x', 'x', 'x']
    """
    return [value] * count


def ee_list_sequence(start, end=None, step=1, count=None):
    """对应 GEE 的 ee.List.sequence()，生成数字序列

    GEE 描述: 生成从 start 到 end（包含）的数字序列，步长为 step。
             如果指定 count，则生成 count 个等间距数字。

    Args:
        start: 起始值
        end: 结束值（包含），可选
        step: 步长（默认为 1）
        count: 生成数量（可选，优先于 end）

    Returns:
        list: 数字序列

    Example:
        >>> ee_list_sequence(1, 5)
        [1, 2, 3, 4, 5]
        >>> ee_list_sequence(0, 10, 2)
        [0, 2, 4, 6, 8, 10]
        >>> ee_list_sequence(0, count=5)
        [0, 1, 2, 3, 4]
    """
    if count is not None:
        if count <= 0:
            return []
        if count == 1:
            return [start]
        if end is not None:
            step_calc = (end - start) / (count - 1)
            return [start + i * step_calc for i in range(count)]
        else:
            return [start + i * step for i in range(count)]

    if end is not None:
        result = []
        current = start
        while (step > 0 and current <= end) or (step < 0 and current >= end):
            result.append(current)
            current += step
        return result

    raise ValueError("必须指定 end 或 count 之一")


def ee_list_size(lst):
    """对应 GEE 的 ee.List.size()，获取列表长度

    GEE 描述: 返回列表中的元素数量。

    Args:
        lst: 列表

    Returns:
        int: 列表长度

    Example:
        >>> ee_list_size([1, 2, 3])
        3
    """
    return len(lst)


def ee_list_slice(lst, start, end=None, step=None):
    """对应 GEE 的 ee.List.slice()，切片列表

    GEE 描述: 返回列表从 start（包含）到 end（排除）的部分。

    Args:
        lst: 列表
        start: 起始索引
        end: 结束索引（排除），可选
        step: 步长，可选

    Returns:
        list: 切片后的列表

    Example:
        >>> ee_list_slice([0, 1, 2, 3, 4, 5], 2, 5)
        [2, 3, 4]
        >>> ee_list_slice([0, 1, 2, 3, 4, 5], 1, None, 2)
        [1, 3, 5]
    """
    if step is not None:
        return lst[start:end:step]
    return lst[start:end]


def ee_list_sort(lst, keys=None):
    """对应 GEE 的 ee.List.sort()，对列表排序

    GEE 描述: 对列表进行排序。可指定排序键。

    Args:
        lst: 列表
        keys: 排序键列表（用于按对象属性排序）

    Returns:
        list: 排序后的列表

    Example:
        >>> ee_list_sort([3, 1, 2])
        [1, 2, 3]
        >>> ee_list_sort([{'v': 3}, {'v': 1}], ['v'])
        [{'v': 1}, {'v': 3}]
    """
    if keys:
        return sorted(lst, key=lambda x: [x.get(k, '') for k in keys] if isinstance(x, dict) else x)
    return sorted(lst)


def ee_listzip(lst, other):
    """对应 GEE 的 ee.List.zip()，将两个列表压缩为元组列表

    GEE 描述: 将两个列表压缩成元组列表。

    Args:
        lst: 第一个列表
        other: 第二个列表

    Returns:
        list: 元组列表 [(elem1, elem2), ...]

    Example:
        >>> ee_listzip([1, 2, 3], ['a', 'b', 'c'])
        [(1, 'a'), (2, 'b'), (3, 'c')]
    """
    return list(zip(lst, other))


# ============================================================
# ee.FeatureCollection.map / iterate -> Python Loop
# ============================================================

def ee_feature_collection_map(collection, algorithm, drop_nulls=False):
    """对应 GEE 的 ee.FeatureCollection.map()，对集合每个元素应用函数

    GEE 描述: 在集合上映射算法，返回包含结果的新集合。

    Args:
        collection: 元素列表（模拟 FeatureCollection）
        algorithm: 映射函数，接收单个元素并返回结果
        drop_nulls: 是否丢弃 None 结果

    Returns:
        list: 映射结果列表

    Example:
        >>> features = [{'name': 'a', 'val': 1}, {'name': 'b', 'val': 2}]
        >>> ee_feature_collection_map(features, lambda f: f['val'] * 10)
        [10, 20]
    """
    result = []
    for element in collection:
        mapped = algorithm(element)
        if mapped is not None or not drop_nulls:
            result.append(mapped)
    return result


def ee_feature_collection_iterate(collection, algorithm, first=None):
    """对应 GEE 的 ee.FeatureCollection.iterate()，在集合上迭代累积

    GEE 描述: 在集合上迭代，将当前元素和前一次迭代结果传给算法函数。
             返回最后一次迭代的结果。

    Args:
        collection: 元素列表
        algorithm: 迭代函数，接收 (element, previous_result) 两个参数
        first: 初始值

    Returns:
        最终迭代结果

    Example:
        >>> items = [1, 2, 3, 4]
        >>> ee_feature_collection_iterate(items, lambda x, y: x + y, 0)
        10
        >>> ee_feature_collection_iterate(items, lambda x, y: x * y, 1)
        24
    """
    result = first
    for element in collection:
        result = algorithm(element, result)
    return result


# ============================================================
# GEE Python 函数注册表
# ============================================================

# GEE API 到 Python 函数的完整映射表
GEE_PYTHON_FUNCTIONS = {
    # print
    'print': gee_print,

    # ee.Array
    'ee.Array': ee_array,
    'ee.Array.matrixDeterminant': ee_array_matrix_determinant,
    'ee.Array.matrixInverse': ee_array_matrix_inverse,
    'ee.Array.matrixTrace': ee_array_matrix_trace,

    # ee.Date
    'ee.Date': ee_date,
    'ee.Date.advance': ee_date_advance,
    'ee.Date.dayOfYear': ee_date_day_of_year,
    'ee.Date.difference': ee_date_difference,
    'ee.Date.format': ee_date_format,
    'ee.Date.get': ee_date_get,
    'ee.Date.getRelative': ee_date_get_relative,
    'ee.Date.parse': ee_date_parse,
    'ee.Date.subtract': ee_date_subtract,
    'ee.DateRange': ee_date_range,

    # ee.Dictionary
    'ee.Dictionary': ee_dictionary,
    'ee.Dictionary.get': ee_dictionary_get,
    'ee.Dictionary.getInfo': ee_dictionary_get_info,
    'ee.Dictionary.set': ee_dictionary_set,
    'ee.Dictionary.toList': ee_dictionary_to_list,

    # ee.FeatureCollection
    'ee.FeatureCollection.iterate': ee_feature_collection_iterate,
    'ee.FeatureCollection.map': ee_feature_collection_map,

    # ee.List
    'ee.List': ee_list,
    'ee.List.contains': ee_list_contains,
    'ee.List.filter': ee_list_filter,
    'ee.List.flatten': ee_list_flatten,
    'ee.List.get': ee_list_get,
    'ee.List.group': ee_list_group,
    'ee.List.join': ee_list_join,
    'ee.List.map': ee_list_map,
    'ee.List.remove': ee_list_remove,
    'ee.List.repeat': ee_list_repeat,
    'ee.List.sequence': ee_list_sequence,
    'ee.List.size': ee_list_size,
    'ee.List.slice': ee_list_slice,
    'ee.List.sort': ee_list_sort,
    'ee.List.zip': ee_listzip,

    # ee.Number
    'ee.Number': ee_number,
    'ee.Number.divide': ee_number_divide,
    'ee.Number.format': ee_number_format,
    'ee.Number.gte': ee_number_gte,
    'ee.Number.lte': ee_number_lte,
    'ee.Number.multiply': ee_number_multiply,

    # ee.String
    'ee.String': ee_string,
    'ee.String.format': ee_string_format,
}


def get_python_function(gee_api_name: str) -> Optional[Callable]:
    """根据 GEE API 名称获取对应的 Python 实现函数

    Args:
        gee_api_name: GEE API 名称（如 'ee.Date.advance'）

    Returns:
        Callable: 对应的 Python 函数，如果不存在返回 None

    Example:
        >>> fn = get_python_function('ee.Date.advance')
        >>> fn is not None
        True
        >>> fn('2023-01-15', 5, 'day')
        datetime.datetime(2023, 1, 20, 0, 0, tzinfo=...)
    """
    return GEE_PYTHON_FUNCTIONS.get(gee_api_name)


def list_all_python_functions() -> List[str]:
    """列出所有已实现的 Python 函数对应的 GEE API 名称

    Returns:
        List[str]: GEE API 名称列表
    """
    return sorted(GEE_PYTHON_FUNCTIONS.keys())


def get_function_info(gee_api_name: str) -> Optional[dict]:
    """获取指定 GEE API 对应的 Python 函数信息

    Args:
        gee_api_name: GEE API 名称

    Returns:
        Optional[dict]: 包含函数名、文档、参数等信息的字典
    """
    fn = GEE_PYTHON_FUNCTIONS.get(gee_api_name)
    if fn is None:
        return None

    import inspect
    sig = inspect.signature(fn)
    return {
        'gee_api': gee_api_name,
        'python_function': fn.__name__,
        'signature': str(sig),
        'doc': fn.__doc__,
        'module': fn.__module__
    }


def generate_implementation_table() -> str:
    """生成所有实现的 GEE API → Python 函数对照表

    Returns:
        str: Markdown 格式的对照表
    """
    lines = ["| GEE API | Python 函数 | 说明 |", "|---------|-------------|------|"]
    for gee_name in sorted(GEE_PYTHON_FUNCTIONS.keys()):
        fn = GEE_PYTHON_FUNCTIONS[gee_name]
        doc_lines = (fn.__doc__ or "").strip().split('\n')
        desc = doc_lines[0] if doc_lines else ""
        lines.append(f"| `{gee_name}` | `{fn.__name__}` | {desc} |")
    return '\n'.join(lines)


if __name__ == '__main__':
    print("GEE → Python 函数实现对照表")
    print("=" * 60)
    print(generate_implementation_table())
    print(f"\n共实现 {len(GEE_PYTHON_FUNCTIONS)} 个 GEE API 的 Python 等价函数")