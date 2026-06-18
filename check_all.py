import django, os, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'vtms_project.settings'
os.environ['DEBUG'] = 'True'
django.setup()

from django.template.loader import get_template
from django.template import TemplateDoesNotExist
import glob

# Find every .html template under core/templates/
templates = glob.glob('core/templates/core/*.html', recursive=False)
print(f'Found {len(templates)} templates\n')

errors = []
for t_path in sorted(templates):
    # Django template name is relative to the templates/ dir, e.g. core/login.html
    t_name = 'core/' + os.path.basename(t_path)
    try:
        get_template(t_name)
        print(f'  OK    {t_name}')
    except TemplateDoesNotExist:
        print(f'  404   {t_name}')
        errors.append((t_name, 'Not found'))
    except Exception as e:
        msg = str(e)
        print(f'  ERROR {t_name}')
        print(f'        {msg[:200]}')
        errors.append((t_name, msg))

print(f'\n{"="*60}')
if errors:
    print(f'{len(errors)} PROBLEM(S) FOUND:')
    for name, err in errors:
        print(f'  {name}:')
        print(f'    {err[:300]}')
else:
    print('All templates compile OK!')
