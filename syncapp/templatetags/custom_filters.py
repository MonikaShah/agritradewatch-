from django import template
from syncapp.forms import DtProduceForm

register = template.Library()

@register.filter
def is_instance(obj, class_name):
    """Check if the object is an instance of a given class name"""
    return obj.__class__.__name__ == class_name

@register.simple_tag
def produce_form(produce):
    form = DtProduceForm(instance=produce)
    for field in form:
        field.field.widget.attrs.update({'class': 'form-control form-control-sm'})
    return form

@register.filter
def split(value, sep=","):
    return value.split(sep)
