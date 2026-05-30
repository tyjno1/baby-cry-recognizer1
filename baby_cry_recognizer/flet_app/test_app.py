# Test script for Flet app
import traceback, sys, os
os.chdir('F:/coding/babylijie/baby_cry_recognizer/flet_app')
sys.path.insert(0, '.')

try:
    from config import NEED_CATEGORIES, MATCH_THRESHOLD, BEHAVIOR_PATTERNS, REFERENCE_GUIDE
    from database import init_db, get_feedback_count
    from audio_processor import extract_features
    from ai_client import DeepSeekClient
    import numpy as np

    init_db()
    count = get_feedback_count()
    print(f'[OK] DB init, feedback count: {count}')

    features = extract_features(np.random.randn(80000).astype(np.float32))
    print(f'[OK] Feature extraction, keys: {list(features.keys())}')

    client = DeepSeekClient()
    print(f'[OK] AI client, configured: {client.is_configured()}')

    print(f'[OK] Need categories: {len(NEED_CATEGORIES)}')
    print(f'[OK] Behaviors: {len(BEHAVIOR_PATTERNS)}')
    print('[OK] ALL TESTS PASSED')
except Exception as e:
    traceback.print_exc()
    print(f'[FAIL] {e}')
    sys.exit(1)
