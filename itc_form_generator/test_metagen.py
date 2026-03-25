#!/usr/bin/env python3
"""
MetaGen Test Script - Verify AI is working on Devserver/NEST

Run this script on a devserver to test MetaGen integration:
    python test_metagen.py

This will:
1. Test MetaGen availability
2. Test AI service initialization
3. Generate sample check items using AI
4. Show comparison between AI and non-AI output
"""

import sys
import json

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def test_metagen_import():
    """Test if MetaGen can be imported."""
    print_header("Test 1: MetaGen Import")
    try:
        from metagen import MetaGenPlatform
        print_success("MetaGen imported successfully!")
        return True
    except ImportError as e:
        print_error(f"MetaGen import failed: {e}")
        print_warning("MetaGen is only available on Meta internal infrastructure.")
        return False

def test_metagen_platform():
    """Test MetaGen platform initialization."""
    print_header("Test 2: MetaGen Platform Initialization")
    try:
        from metagen import MetaGenPlatform
        platform = MetaGenPlatform()
        print_success("MetaGen platform initialized!")

        # Try to get available models
        try:
            models = platform.list_models() if hasattr(platform, 'list_models') else None
            if models:
                print(f"   Available models: {models[:3]}...")
        except:
            pass

        return platform
    except Exception as e:
        print_error(f"Platform initialization failed: {e}")
        return None

def test_simple_completion(platform):
    """Test a simple chat completion."""
    print_header("Test 3: Simple Chat Completion")
    try:
        response = platform.chat_completion(
            model_name="llama-3.3-70b",
            messages=[{
                "role": "user",
                "content": "Say 'MetaGen is working!' and nothing else."
            }],
            temperature=0.1,
            max_tokens=50
        )

        content = response.content if hasattr(response, 'content') else str(response)
        print_success(f"Response: {content}")
        return True
    except Exception as e:
        print_error(f"Chat completion failed: {e}")
        return False

def test_ai_service():
    """Test the AI service module."""
    print_header("Test 4: AI Service Module")
    try:
        # Add src to path
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

        from itc_form_generator.ai_service import AIService, AIConfig

        service = AIService()

        if service.is_available:
            print_success("AI Service is available!")
            print(f"   Model: {service.config.model}")
            print(f"   Temperature: {service.config.temperature}")
            return service
        else:
            print_warning("AI Service initialized but MetaGen not available")
            return None
    except Exception as e:
        print_error(f"AI Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_generate_check_items(service):
    """Test generating check items with AI."""
    print_header("Test 5: AI Check Item Generation")

    # Sample system info
    system_info = {
        'name': 'Air Handling Unit',
        'tag': 'AHU-01',
        'components': [
            {'tag': 'SF-01', 'name': 'Supply Fan', 'type': 'fan'},
            {'tag': 'RF-01', 'name': 'Return Fan', 'type': 'fan'},
            {'tag': 'CC-01', 'name': 'Cooling Coil', 'type': 'coil'}
        ],
        'setpoints': [
            {'name': 'Supply Air Temp', 'value': '55', 'units': '°F'},
            {'name': 'Static Pressure', 'value': '1.5', 'units': 'inWC'}
        ],
        'operating_modes': [
            {'name': 'Occupied', 'conditions': ['Schedule ON'], 'actions': ['Normal operation']},
            {'name': 'Unoccupied', 'conditions': ['Schedule OFF'], 'actions': ['Setback mode']}
        ],
        'interlocks': ['Smoke detector shutdown', 'Fire alarm shutdown']
    }

    try:
        print("Generating check items for AHU-01...")
        print("(This may take 10-30 seconds)")

        items = service.generate_check_items(system_info, 'ITC')

        if items:
            print_success(f"Generated {len(items)} check items!")
            print("\nSample items:")
            for i, item in enumerate(items[:5]):
                print(f"\n   {i+1}. {item.get('description', 'N/A')[:80]}...")
                print(f"      Type: {item.get('check_type', 'N/A')}")
                print(f"      Priority: {item.get('priority', 'N/A')}")
                print(f"      Criteria: {item.get('acceptance_criteria', 'N/A')[:60]}...")
            return True
        else:
            print_warning("No items generated (AI may have returned empty response)")
            return False
    except Exception as e:
        print_error(f"Check item generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_soo_parsing(service):
    """Test AI-enhanced SOO parsing."""
    print_header("Test 6: AI SOO Parsing")

    sample_soo = """
    # Air Handling Unit AHU-01

    ## Components
    - Supply Fan (SF-01): Variable speed supply fan
    - Return Fan (RF-01): Variable speed return fan
    - Cooling Coil (CC-01): Chilled water cooling coil
    - Heating Coil (HC-01): Hot water heating coil

    ## Setpoints
    - Supply Air Temperature Setpoint: 55°F (adjustable 50-65°F)
    - Static Pressure Setpoint: 1.5 inWC (adjustable 0.5-2.5 inWC)
    - Return Air Temperature High Limit: 80°F

    ## Operating Modes
    ### Occupied Mode
    When the schedule is ON, the AHU operates in occupied mode:
    - Supply fan runs at speed required to maintain static pressure
    - Temperature control active

    ### Unoccupied Mode
    When schedule is OFF:
    - Supply fan cycles to maintain setback temperature
    - Minimum outdoor air damper closed
    """

    try:
        print("Parsing sample SOO with AI...")
        result = service.parse_soo_document(sample_soo)

        if result:
            print_success("SOO parsed successfully!")
            print(f"\nExtracted data:")
            print(json.dumps(result, indent=2)[:500] + "...")
            return True
        else:
            print_warning("AI parsing returned no result")
            return False
    except Exception as e:
        print_error(f"SOO parsing failed: {e}")
        return False

def run_all_tests():
    """Run all MetaGen tests."""
    print_header("MetaGen Integration Test Suite")
    print("Testing MetaGen AI integration on this machine...")

    results = {
        'import': False,
        'platform': False,
        'completion': False,
        'ai_service': False,
        'check_items': False,
        'soo_parsing': False
    }

    # Test 1: Import
    results['import'] = test_metagen_import()

    if not results['import']:
        print_header("Test Results Summary")
        print_error("MetaGen is NOT available on this machine.")
        print("\nMetaGen only works on:")
        print("  - Meta Devservers")
        print("  - OnDemand (OD) instances")
        print("  - NEST deployments")
        print("\nThe app will use feedback-based enhancements instead.")
        return results

    # Test 2: Platform
    platform = test_metagen_platform()
    results['platform'] = platform is not None

    if not results['platform']:
        return results

    # Test 3: Simple completion
    results['completion'] = test_simple_completion(platform)

    # Test 4: AI Service
    service = test_ai_service()
    results['ai_service'] = service is not None

    if service:
        # Test 5: Check items
        results['check_items'] = test_generate_check_items(service)

        # Test 6: SOO parsing
        results['soo_parsing'] = test_soo_parsing(service)

    # Summary
    print_header("Test Results Summary")

    passed = sum(results.values())
    total = len(results)

    for test, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {test}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print_success("\n🎉 All tests passed! MetaGen is fully functional!")
        print("\nYou can now use AI-enhanced form generation:")
        print("  1. Open the webapp")
        print("  2. Check 'Enable AI Enhancement'")
        print("  3. Upload your SOO document")
        print("  4. Get AI-generated check items!")
    elif passed > 0:
        print_warning("\n⚠️  Some tests failed. Check the errors above.")
    else:
        print_error("\n❌ All tests failed. MetaGen is not working.")

    return results

if __name__ == "__main__":
    run_all_tests()
