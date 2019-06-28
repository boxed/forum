

container__attrs__class={'t-input': True},
label_container__tag=None,

# base definition, See compact_form_row.html in tri.form
container = Content(
    tag='div',
    children=dict(
        label=Content(tag='div', ...),
        input=Content(tag='span', ...),
        errors=Content(...),
    )
)

# triDS override. See compact_form_row.html in triresolve
container.post_process_children=lambda children, content, **_: Content(
    tag=content.tag,
    attrs=content.attrs,
    children=dict(
        label=children.label,
        input_container=Content(
            children=dict(
                input=children.input,
                errors=children.errors,
            )
        )
    )
)
