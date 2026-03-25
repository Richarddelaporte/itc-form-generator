"""
ITC Form Generator — Command Line Interface

Provides CLI entry points for running the web application
and performing batch form generation from the terminal.

Usage:
    itc-form-generator                    # Start web UI (default)
    itc-form-generator serve              # Start web server
    itc-form-generator serve --port 5000  # Custom port
    itc-form-generator generate SOO.md    # Batch generate from SOO
    itc-form-generator generate SOO.md --points points.csv  # With points list
    itc-form-generator generate SOO.md --output ./forms/    # Custom output dir
    itc-form-generator --version          # Show version
"""

import argparse
import os
import sys
import webbrowser
import logging
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='itc-form-generator',
        description='AI-powered ITC Form Generator for HVAC/BMS commissioning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  itc-form-generator                         Start web interface
  itc-form-generator serve --port 5000       Start on custom port
  itc-form-generator generate soo.md         Generate forms from SOO document
  itc-form-generator generate soo.md -p pts.csv -o ./output/
        """
    )

    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start the web server')
    serve_parser.add_argument('--host', default='127.0.0.1', help='Host to bind (default: 127.0.0.1)')
    serve_parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    serve_parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    serve_parser.add_argument('--production', action='store_true', help='Run in production mode with gunicorn')
    serve_parser.add_argument('--workers', type=int, default=None, help='Number of gunicorn workers')

    # Generate command (batch mode)
    gen_parser = subparsers.add_parser('generate', help='Generate forms from SOO document (batch mode)')
    gen_parser.add_argument('soo_file', help='Path to SOO document (.md, .txt, .pdf)')
    gen_parser.add_argument('-p', '--points', help='Path to points list (.csv, .xlsx)')
    gen_parser.add_argument('-o', '--output', default='./itc_output', help='Output directory (default: ./itc_output)')
    gen_parser.add_argument('--project', default='', help='Project number')
    gen_parser.add_argument('--building', default='', help='Building/area name')
    gen_parser.add_argument('--no-ai', action='store_true', help='Disable AI-enhanced parsing')
    gen_parser.add_argument('--format', choices=['html', 'excel', 'csv', 'all'], default='all',
                           help='Output format (default: all)')

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    # Default: start web server
    if args.command is None or args.command == 'serve':
        _cmd_serve(args)
    elif args.command == 'generate':
        _cmd_generate(args)
    else:
        parser.print_help()


def _cmd_serve(args):
    """Start the web server."""
    host = getattr(args, 'host', '127.0.0.1')
    port = getattr(args, 'port', 8080)
    no_browser = getattr(args, 'no_browser', False)
    production = getattr(args, 'production', False)

    if production:
        _serve_production(host, port, getattr(args, 'workers', None))
    else:
        _serve_development(host, port, no_browser)


def _serve_development(host, port, no_browser=False):
    """Start Flask development server."""
    print(f"""
╔══════════════════════════════════════════════╗
║       ITC Form Generator v2.0.0             ║
║                                             ║
║  🌐 http://{host}:{port}                   ║
║  📋 Upload SOO → Generate ITC Forms         ║
║                                             ║
║  Press Ctrl+C to stop                       ║
╚══════════════════════════════════════════════╝
""")

    if not no_browser:
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://{host}:{port}')
        threading.Thread(target=open_browser, daemon=True).start()

    from app import create_app
    app = create_app('development')
    app.run(host=host, port=port, debug=True, use_reloader=False)


def _serve_production(host, port, workers=None):
    """Start gunicorn production server."""
    import subprocess
    import multiprocessing

    workers = workers or min(multiprocessing.cpu_count() * 2 + 1, 4)
    cmd = [
        sys.executable, '-m', 'gunicorn',
        'wsgi:app',
        f'--bind={host}:{port}',
        f'--workers={workers}',
        '--timeout=120',
        '--access-logfile=-',
    ]
    print(f"Starting production server: {' '.join(cmd)}")
    subprocess.run(cmd)


def _cmd_generate(args):
    """Batch generate forms from command line."""
    soo_path = Path(args.soo_file)
    if not soo_path.exists():
        print(f"Error: SOO file not found: {soo_path}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"""
╔══════════════════════════════════════════════╗
║       ITC Form Generator v2.0.0             ║
║       Batch Generation Mode                 ║
╚══════════════════════════════════════════════╝

  📄 SOO:     {soo_path.name}
  📊 Points:  {args.points or 'None'}
  📁 Output:  {output_dir}
  🤖 AI:      {'Enabled' if not args.no_ai else 'Disabled'}
""")

    from itc_form_generator.parser import SOOParser
    from itc_form_generator.form_generator import FormGenerator
    from itc_form_generator.exporter import FormExporter

    use_ai = not args.no_ai

    # Read SOO document
    ext = soo_path.suffix.lower()
    if ext == '.pdf':
        from itc_form_generator.pdf_parser import PDFParser
        soo_content = PDFParser().parse(str(soo_path))
    else:
        soo_content = soo_path.read_text(encoding='utf-8', errors='replace')

    if not soo_content.strip():
        print("Error: SOO document is empty")
        sys.exit(1)

    # Parse SOO
    print("  ⏳ Parsing SOO document...")
    parser = SOOParser(use_ai=use_ai)
    soo_data = parser.parse(soo_content)
    print(f"  ✅ Found {len(soo_data.systems) if hasattr(soo_data, 'systems') else 0} systems")

    # Parse points list if provided
    points_list = None
    if args.points:
        pts_path = Path(args.points)
        if pts_path.exists():
            print(f"  ⏳ Parsing points list ({pts_path.name})...")
            from itc_form_generator.points_parser import PointsListParser
            pts_parser = PointsListParser()
            if pts_path.suffix.lower() in ('.csv', '.tsv'):
                pts_content = pts_path.read_text(encoding='utf-8', errors='replace')
                points_list = pts_parser.parse(pts_content, pts_path.name)
            else:
                points_list = pts_parser.parse(str(pts_path), pts_path.name)
            print(f"  ✅ Found {len(points_list.points)} points")
        else:
            print(f"  ⚠️  Points file not found: {pts_path}")

    # Generate forms
    print("  ⏳ Generating forms...")
    generator = FormGenerator(use_ai=use_ai)
    forms = generator.generate(
        soo_data=soo_data,
        project_number=args.project,
        building_area=args.building,
        points_list=points_list,
    )
    print(f"  ✅ Generated {len(forms)} forms")

    # Export
    exporter = FormExporter()
    from itc_form_generator.renderer import HTMLRenderer
    renderer = HTMLRenderer()
    fmt = args.format

    exported_count = 0
    for form in forms:
        name = form.get('name', 'form').replace(' ', '_')
        sys_type = form.get('system_type', 'generic')
        base_name = f"{sys_type}_{name}"

        if fmt in ('html', 'all'):
            html_path = output_dir / f"{base_name}.html"
            html_content = renderer.render(form)
            html_path.write_text(html_content, encoding='utf-8')
            exported_count += 1
            print(f"    📄 {html_path.name}")

        if fmt in ('excel', 'all'):
            try:
                xlsx_path = output_dir / f"{base_name}.xlsx"
                exporter.export_to_excel(form, str(xlsx_path))
                exported_count += 1
                print(f"    📊 {xlsx_path.name}")
            except Exception as e:
                print(f"    ⚠️  Excel export failed: {e}")

        if fmt in ('csv', 'all'):
            try:
                csv_path = output_dir / f"{base_name}.csv"
                exporter.export_to_csv(form, str(csv_path))
                exported_count += 1
                print(f"    📋 {csv_path.name}")
            except Exception as e:
                print(f"    ⚠️  CSV export failed: {e}")

    print(f"""
  ✅ Done! Exported {exported_count} files to {output_dir}
""")


if __name__ == '__main__':
    main()

