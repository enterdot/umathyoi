import re


def pascal_case_to_kebab_case(string):
    return re.sub(r"([A-Z])", r"-\1", string).lower().lstrip("-")


def pascal_case_to_title_case(string):
    return re.sub(r"([A-Z])", r" \1", string).strip()


def auto_tag_from_instance(i):
    return pascal_case_to_kebab_case(i.__class__.__name__)


def auto_title_from_instance(i):
    return pascal_case_to_title_case(i.__class__.__name__)
