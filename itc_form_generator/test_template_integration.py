"""Test form generation with RSB/ATS equipment in SOO."""

import sys
import os

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from itc_form_generator.parser import SOOParser
from itc_form_generator.form_generator import FormGenerator


def test_electrical_form_generation():
    """Test form generation with electrical equipment SOO."""

    print("=" * 70)
    print("Testing Form Generation with RSB/ATS Equipment")
    print("=" * 70)

    # Read the test SOO
    soo_path = os.path.join(os.path.dirname(__file__), 'test_electrical_soo.md')
    with open(soo_path, 'r') as f:
        soo_content = f.read()

    print(f"\n[DOC] Loaded SOO from: {soo_path}")

    # Parse the SOO
    parser = SOOParser()
    soo = parser.parse(soo_content)

    print(f"\n[PARSE] Parsed {len(soo.systems)} systems:")
    for system in soo.systems:
        print(f"   - {system.name}")
        print(f"     Tag: {system.tag}")
        print(f"     Components: {len(system.components)}")
        print(f"     Setpoints: {len(system.setpoints)}")
        print(f"     Operating Modes: {len(system.operating_modes)}")
        print(f"     Interlocks: {len(system.interlocks)}")
        print(f"     Alarms: {len(system.alarms)}")

    # Generate forms
    print("\n" + "=" * 70)
    print("Generating ITC Forms with Template Integration")
    print("=" * 70)

    generator = FormGenerator(soo)

    # Test equipment detection
    print("\n[DETECT] Equipment Type Detection:")
    for system in soo.systems:
        equip_type = generator._get_equipment_type_from_system(system)
        print(f"   {system.name[:50]}... -> {equip_type}")

    # Generate forms
    forms = generator.generate_all_forms()

    print(f"\n[FORMS] Generated {len(forms)} forms:")

    for form in forms:
        print(f"\n{'-' * 60}")
        print(f"[FORM] {form.title}")
        print(f"   System: {form.system}")
        print(f"   Sections: {len(form.sections)}")
        print(f"   Total Items: {form.total_items}")

        print(f"\n   [SECTIONS]:")
        for section in form.sections:
            item_count = len(section.check_items)
            # Check for template items
            template_items = sum(1 for item in section.check_items if item.id.startswith("TPL-"))
            enhanced_items = sum(1 for item in section.check_items if item.id.startswith("ENH-"))
            eot_items = sum(1 for item in section.check_items if item.id.startswith("EOT-"))

            badge = ""
            if template_items > 0:
                badge += f" [TPL:{template_items}]"
            if enhanced_items > 0:
                badge += f" [ENH:{enhanced_items}]"
            if eot_items > 0:
                badge += f" [EOT:{eot_items}]"

            print(f"      * {section.title}: {item_count} items{badge}")

            # Show first few template items as examples
            if template_items > 0:
                print(f"        Sample template items:")
                shown = 0
                for item in section.check_items:
                    if item.id.startswith("TPL-") and shown < 3:
                        desc = item.description[:60] if len(item.description) > 60 else item.description
                        print(f"          - {desc}...")
                        shown += 1

    # Test template integration details
    print("\n" + "=" * 70)
    print("Template Integration Details")
    print("=" * 70)

    try:
        from itc_form_generator.template_integration import (
            detect_equipment_type,
            extract_equipment_details,
            get_template_integrator,
        )

        integrator = get_template_integrator()

        for system in soo.systems:
            equip_type = detect_equipment_type(system.name, system.tag or "")
            details = extract_equipment_details(system.name)

            print(f"\n[EQUIP] {system.name[:50]}...")
            print(f"   Equipment Type: {equip_type or 'Not detected'}")
            print(f"   Details: {details}")

            if equip_type:
                sections = integrator.get_template_sections(
                    equip_type,
                    level=details.get("level", "L3"),
                    area=details.get("area", ""),
                    identifier=details.get("identifier", ""),
                    variant=details.get("variant", ""),
                )
                print(f"   Template Sections: {len(sections)}")
                for section in sections:
                    print(f"      * {section.display_name}: {len(section.items)} items ({section.usage_count:,} uses)")

    except Exception as e:
        print(f"   Error in template integration: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("[OK] Test Complete!")
    print("=" * 70)

    return forms


if __name__ == "__main__":
    forms = test_electrical_form_generation()
