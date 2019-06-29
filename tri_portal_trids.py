from tri_struct import Struct

from tri_portal_3 import bind

# base definition, See compact_form_row.html in tri.form
container = dict(
    tag='div',
    children=dict(
        label=dict(tag='div', content='label!'),
        input=dict(tag='span', content='input!'),
        errors=dict(content='errors!'),
    )
)

request = Struct()

assert bind(**container).render2(request) == """<div>
<div>label!</div>
<span>input!</span>
errors!
</div>"""

# triDS override. See compact_form_row.html in triresolve
triDS = bind(
    **container,
    attrs__class={'t-input': True},
    children__label__tag=None,  # this is "label_container" in existing tri.form
    post_process__children=lambda children, content, **_: dict(
        label=children.label,
        input_container=dict(
            tag='div',
            children=dict(
                input=children.input,
                errors=children.errors,
            )
        )
    )
)

expected = """<div class="t-input">
label!
<div>
<span>input!</span>
errors!
</div>
</div>"""

assert triDS.render2(request) == expected
