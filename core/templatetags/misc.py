# -*- coding: utf-8 -*-
from django import template


register = template.Library()


@register.filter
def next(some_list, current_index):
    """
    Returns the element at the next index of the zero-indexed list
    :param some_list: a list
    :param current_index: the current index to increment
    :returns: the element at the next index or an empty string
    """
    if not some_list or current_index >= len(some_list) - 1:
        return ""
    return some_list[current_index + 1]


@register.filter
def prev(some_list, current_index):
    """
    Returns the element at the previous index of the zero-indexed list
    :param some_list: a list
    :param current_index: the current index to decrement
    :returns: the element at the previous index or an empty string
    """
    if not some_list or current_index <= 0:
        return ""
    return some_list[current_index - 1]
