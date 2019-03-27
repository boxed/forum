from django.db import transaction, connection

from wiki.models import Context, Document, DocumentVersion


@transaction.atomic
def import_from_skforum():
    cursor = connection.cursor()
    # for table in ['forum_message', 'forum_room', 'unread_usertime', 'unread_systemtime']:
    #     cursor.execute(f'truncate {table}')

    from ftfy import fix_text, guess_bytes

    cursor.execute('select CONTEXT, DOCKEY, VERSION, CONTENT from forum.documentversioncontent2')

    for context, dockey, version, content in cursor.fetchall():
        try:
            # if name in an int, then it's a personal wiki for the user of that pk
            int(context)
            context = Context.objects.get_or_create(name=context, custom_data=f'user/{context}')[0]
        except ValueError:
            context = Context.objects.get_or_create(name=context)[0]

        document = Document.objects.get_or_create(context=context, name=dockey)[0]
        DocumentVersion.objects.get_or_create(document=document, version=int(version), content=fix_text(guess_bytes(content)[0]))

    for context in Context.objects.all():
        try:
            int(context.name)
            context.name = 'Private wiki'
            context.save()
        except ValueError:
            pass

    # TODO: times
