#!/usr/bin/env python

import os

filenames = set()

for root, dirs, files in os.walk('.'):
    if 'venv' in dirs:
        dirs.remove('venv')
    for f in files:
        if f.endswith('.html'):
            filenames.add(f)

for root, dirs, files in os.walk('.'):
    if 'venv' in dirs:
        dirs.remove('venv')
    for f in files:
        if f.endswith('.py') or f.endswith('.html'):
            content = open(os.path.join(root, f)).read()
            found = {x for x in filenames if x in content}
            filenames -= found

whitelist = [

]

filenames = [x for x in filenames if x not in whitelist]

print(f'{len(filenames)} unused templates:')
print('')
for x in sorted(filenames):
    print(x)
