# Scripts

Utility scripts for the ReCall project.

## build_translations.py

Compiles `.ts` translation source files to `.qm` binary files used at runtime.

```bash
python scripts/build_translations.py
```

Run this after editing any `.ts` file in `resources/translations/`.

## setup_data.py

Initializes a database with a sample exam structure (CompTIA A+ 220-1101/1102 modules and chapters).

```bash
# Populate default.db with a sample exam structure
python scripts/setup_data.py

# Create an empty template database
python scripts/setup_data.py --template data/my_exam.db
```
