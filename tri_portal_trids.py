from tri_declarative import (
    Namespace,
    dispatch,
    Shortcut,
)
from tri_struct import Struct

from tri_portal_3 import bind

container__attrs__class={'t-input': True},
label_container__tag=None,

Content = Namespace



label = Shortcut(
    tag='label',
    attrs__for=lambda field, **_: field.id,
    children__text=lambda field, **_: field.display_name,
)

request = Struct()

field = Namespace(id='foo', display_name='display_name')
assert bind(**Content(tag='div', children=dict(label=label))).render2(request) == '''<div>
<link for="foo">
display_name
</link>
</div>'''
exit(1)


@dispatch(
    tag='input',
    no_end_tag=True,
)
def input(field, **kwargs):
    return Namespace(
        attrs=dict(
            type=field.input_type,
            value=field.rendered_value,  # TODO: but late evaluated right?
            name=field.name,
            id=field.id,
        ),
        children=dict(
            text=field.display_name,
        ),
        **kwargs
    )


# base definition, See compact_form_row.html in tri.form
container = Content(
    tag='div',
    children=dict(
        label_container=Content(
            tag='div',
            children=dict(label=label(field)),
        ),
        input_container=Content(
            tag='span',
            children=dict(
                input=input(field)
            )
        ),
        errors=Content(...),
    )
)

# # triDS override. See compact_form_row.html in triresolve
# container.post_process_children=lambda children, content, **_: Content(
#     tag=content.tag,
#     attrs=content.attrs,
#     children=dict(
#         label=children.label,
#         input_container=Content(
#             children=dict(
#                 input=children.input,
#                 errors=children.errors,
#             )
#         )
#     )
# )
#
#
# ## This is another idea for how to restructure:
# # structure=[
# #     'label',
# #     ['input', 'errors']
# # ]
