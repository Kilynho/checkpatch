import os
import glob
import json
import unittest

def review_python_files():
    results = []
    for pyfile in glob.glob('src/**/*.py', recursive=True):
        with open(pyfile, encoding='utf-8') as f:
            content = f.read()
            # Simple checks
            issues = []
            if 'TODO' in content:
                issues.append('Contiene TODO')
            if 'print(' in content:
                issues.append('Uso de print en producción')
            results.append({'file': pyfile, 'issues': issues})
    return results

def review_html_files():
    results = []
    for htmlfile in glob.glob('src/**/*.html', recursive=True):
        with open(htmlfile, encoding='utf-8') as f:
            content = f.read()
            issues = []
            if '<script>' in content:
                issues.append('Uso de <script> detectado')
            results.append({'file': htmlfile, 'issues': issues})
    return results

def review_json_files():
    results = []
    for jsonfile in glob.glob('src/**/*.json', recursive=True):
        try:
            with open(jsonfile, encoding='utf-8') as f:
                json.load(f)
        except Exception as e:
            results.append({'file': jsonfile, 'issues': [f'Error de formato: {str(e)}']})
        else:
            results.append({'file': jsonfile, 'issues': []})
    return results

def run_unittests():
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return {
        'testsRun': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'successful': result.wasSuccessful()
    }

def report(results):
    print("==== RESULTADOS DE LA REVISIÓN ====")
    for section, items in results.items():
        print(f"\n*** {section.upper()} ***")
        if section == 'tests':
            print(json.dumps(items, indent=2))
        else:
            for item in items:
                if item['issues']:
                    print(f"{item['file']} → {item['issues']}")

if __name__ == '__main__':
    results = {}
    results['python'] = review_python_files()
    results['html'] = review_html_files()
    results['json'] = review_json_files()
    results['tests'] = run_unittests()
    report(results)
