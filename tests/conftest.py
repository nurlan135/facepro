"""
FacePro Test Fixtures
Shared fixtures for all tests.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def temp_db_path():
    """
    Test üçün müvəqqəti database faylı yaradır.
    Test bitdikdən sonra fayl silinir.
    """
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    yield path
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def temp_db(temp_db_path):
    """
    Test üçün müvəqqəti database yaradır.
    DatabaseManager istifadə edir.
    """
    # Set environment variable for test database
    original_path = os.environ.get('FACEPRO_DB_PATH')
    os.environ['FACEPRO_DB_PATH'] = temp_db_path
    
    # Lazy import to avoid circular imports
    from src.core.database.db_manager import get_db_manager
    
    db = get_db_manager()
    
    yield db
    
    # Cleanup
    try:
        db.close_connection()
    except:
        pass
    
    if original_path:
        os.environ['FACEPRO_DB_PATH'] = original_path
    elif 'FACEPRO_DB_PATH' in os.environ:
        del os.environ['FACEPRO_DB_PATH']


@pytest.fixture
def mock_storage_worker():
    """Mock StorageWorker for testing."""
    mock = Mock()
    mock.add_reid_task = Mock()
    mock.add_gait_task = Mock()
    mock.add_task = Mock()
    return mock


@pytest.fixture
def mock_frame():
    """Generate a dummy video frame for testing."""
    import numpy as np
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_person_crop():
    """Generate a dummy person crop for testing."""
    import numpy as np
    return np.random.randint(0, 255, (300, 150, 3), dtype=np.uint8)


@pytest.fixture
def mock_face_image():
    """Generate a dummy face image for testing."""
    import numpy as np
    return np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)


@pytest.fixture
def sample_detection():
    """Create a sample Detection object for testing."""
    from src.core.detection import Detection, DetectionType
    
    return Detection(
        type=DetectionType.PERSON,
        bbox=(100, 100, 300, 400),
        confidence=0.85,
        track_id=42
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances between tests.
    This ensures test isolation.
    """
    yield
    
    # Reset singletons after test
    try:
        from src.core.reid_engine import ReIDEngine
        ReIDEngine._instance = None
    except:
        pass
    
    try:
        from src.core.gait_engine import GaitEngine
        GaitEngine._instance = None
    except:
        pass
