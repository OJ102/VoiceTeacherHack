#!/usr/bin/env python3
"""Test script to verify Voice Teaching Agent setup."""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required keys."""
    env_file = Path(__file__).parent / ".env"
    print("\n📋 Environment Variables Check")
    print("-" * 40)

    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then edit .env with your API keys")
        return False

    print("✅ .env file found")

    required_keys = [
        "OPENAI_API_KEY",
        "TAVILY_API_KEY",
        "MODULATE_API_KEY",
        "PLIVO_AUTH_ID",
        "PLIVO_AUTH_TOKEN",
    ]

    from dotenv import load_dotenv
    load_dotenv(env_file)

    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
            print(f"❌ Missing: {key}")
        else:
            # Show masked value
            val = os.getenv(key)
            masked = val[:4] + "*" * (len(val) - 8) + val[-4:] if len(val) > 8 else "***"
            print(f"✅ {key}: {masked}")

    return len(missing) == 0


def check_python_modules():
    """Check if required Python modules can be imported."""
    print("\n📚 Python Modules Check")
    print("-" * 40)

    modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("websockets", "WebSockets"),
        ("pydantic", "Pydantic"),
        ("tavily", "Tavily"),
        ("openai", "OpenAI"),
        ("gtts", "gTTS"),
        ("plivo", "Plivo"),
        ("dotenv", "python-dotenv"),
    ]

    all_ok = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - not installed")
            all_ok = False

    return all_ok


def check_backend_modules():
    """Check if backend modules can be imported."""
    print("\n🔧 Backend Modules Check")
    print("-" * 40)

    sys.path.insert(0, str(Path(__file__).parent))

    modules = [
        ("transcriber", "PlivoTranscriber"),
        ("tavily_integration", "TavilySearch"),
        ("modulate_integration", "ModulateEmotionDetector"),
        ("tts_engine", "TTSEngine"),
        ("teacher_agent", "TeachingAgent"),
    ]

    all_ok = True
    for module, class_name in modules:
        try:
            mod = __import__(module)
            getattr(mod, class_name)
            print(f"✅ {module}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"❌ {module}.{class_name} - {e}")
            all_ok = False

    return all_ok


def main():
    """Run all checks."""
    print("\n" + "="*40)
    print("Voice Teaching Agent - Setup Check")
    print("="*40)

    checks = [
        ("Environment", check_env_file),
        ("Python Modules", check_python_modules),
        ("Backend Modules", check_backend_modules),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results.append((name, False))

    print("\n" + "="*40)
    print("Summary")
    print("="*40)

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    if all_passed:
        print("\n🎉 All checks passed! Ready to run.")
        print("\nNext steps:")
        print("1. Terminal 1: python -m uvicorn main:app --reload --port 8000")
        print("2. Terminal 2: cd ../frontend && python -m http.server 8001")
        print("3. Open: http://localhost:8001")
    else:
        print("\n⚠️  Fix the issues above before running the server.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
