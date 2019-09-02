from tri_declarative import (
    Namespace,
    dispatch,
    Shortcut,
)
from tri_form import (
    Field,
    Form,
)
from tri_struct import Struct

from tri_portal_3 import (
    bind,
    BoundContent,
)

container__attrs__class={'t-input': True},
label_container__tag=None,

Content = Namespace

label = Shortcut(
    tag='label',
    attrs__for=lambda field, **_: field.id,
    content=lambda field, **_: field.display_name,
)

request = Struct()


class MyForm(Form):
    foo = Field()


form = MyForm()

field = form.fields_by_name.foo

actual = bind(**Content(tag='div', children=dict(label=label), evaluate_with=dict(field=field))).render2(request).strip()

expected = '''<div>
<label for="id_foo">Foo</label>
</div>'''

assert expected == actual, actual


input = Shortcut(
    tag='input',
    end_tag=False,
    attrs=dict(
        type=lambda field, **_: field.input_type,
        value=lambda field, **_: field.rendered_value,
        name=lambda field, **_: field.name,
        id=lambda field, **_: field.id,
    ),
)

assert bind(**input, evaluate_with=dict(field=field)).render2(request) == '<input id="id_foo" name="foo" type="text" value="">'


errors = Shortcut(
    show=lambda field, **_: field.errors,
    tag='ul',
    children=lambda field, **_: {error: BoundContent(tag='li', content=error) for error in field.errors},
)

# base definition, See compact_form_row.html in tri.form
container = Content(
    tag='div',
    children=dict(
        label_container=Content(
            tag='div',
            children=dict(label=label),
        ),
        input_container=Content(
            tag='span',
            children=dict(
                input=input
            )
        ),
        errors=errors
    )
)

actual = bind(**container, evaluate_with=dict(field=field)).render2(request)

assert actual == '''<div>
<div>
<label for="id_foo">Foo</label>
</div>
<span>
<input id="id_foo" name="foo" type="text" value="">
</span>
</div>'''


# triDS override. See compact_form_row.html in triresolve
actual = bind(**container, post_process_children=lambda children, bound_content, **_: Content(
    tag=bound_content.tag,
    attrs=bound_content.attrs,
    children=dict(
        label=children.label_container.children.label,
        input_container=Content(
            children=dict(
                input=children.input_container.children.input,
                errors=children.errors,
            )
        )
    )
)).render2(request)



# Test rendering with an error
field.errors.add('asd!')

actual = bind(**container, evaluate_with=dict(field=field)).render2(request)

assert actual == '''<div>
<div>
<label for="id_foo">Foo</label>
</div>
<span>
<input id="id_foo" name="foo" type="text">
</span>
<ul>
<li>asd!</li>
</ul>
</div>''', actual


# This is another idea for how to restructure:

# structure = '''
# div container
#     div label_container
#         label
#     span input_container
#         input
#     errors
# '''
#
# override_structure = '''
# div container
#     label
#     div input_container
#         input
#         errors
# '''


# structure=[
#     'label',
#     ['input', 'errors']
# ]
