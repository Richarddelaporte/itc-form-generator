"""
ITC Form Generator — AI-powered commissioning form generator.

Usage:
    # As a library
    from itc_form_generator.parser import SOOParser
    from itc_form_generator.form_generator import FormGenerator

    parser = SOOParser(use_ai=True)
    soo_data = parser.parse(soo_text)
    generator = FormGenerator(use_ai=True)
    forms = generator.generate(soo_data)

    # As a web app
    from app import create_app
    app = create_app()
    app.run()
"""

__version__ = "2.0.0"
__author__ = "Richard Delaporte"

