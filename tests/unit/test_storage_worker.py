
import pytest
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock
from src.core.storage_worker import StorageWorker, TaskType
from src.core.detection import Detection, DetectionType

class TestStorageWorker:
    @pytest.fixture
    def worker(self):
        worker = StorageWorker()
        
        # Mock repositories
        worker._event_repo = Mock()
        worker._embedding_repo = Mock()
        
        # Prevent actual run loop for unit tests unless needed
        worker._running = True 
        
        return worker

    def test_initialization(self, worker):
        assert worker is not None
        assert worker._task_queue.empty()

    def test_add_event_task(self, worker, sample_detection, mock_frame):
        worker.add_event_task(sample_detection, mock_frame)
        
        assert not worker._task_queue.empty()
        task = worker._task_queue.get()
        assert task['type'] == TaskType.EVENT
        assert task['data']['detection'] == sample_detection
        # Use simple assert equal for arrays if small, or specific numpy testing
        np.testing.assert_array_equal(task['data']['frame'], mock_frame)
        
    def test_add_reid_task(self, worker):
        vector = np.zeros((512,))
        user_id = 1
        
        worker.add_reid_task(user_id, vector)
        
        task = worker._task_queue.get()
        assert task['type'] == TaskType.REID
        assert task['data']['user_id'] == user_id
        np.testing.assert_array_equal(task['data']['vector'], vector)

    def test_add_gait_task(self, worker):
        embedding = np.zeros((128,))
        user_id = 99
        
        worker.add_gait_task(user_id, embedding)
        
        task = worker._task_queue.get()
        assert task['type'] == TaskType.GAIT
        assert task['data']['user_id'] == user_id
        np.testing.assert_array_equal(task['data']['embedding'], embedding)

    @patch('src.core.storage_worker.save_snapshot')
    def test_process_event_task(self, mock_save_snapshot, worker, sample_detection, mock_frame):
        # Setup mocks
        mock_save_snapshot.return_value = "/path/to/snapshot.jpg"
        worker._event_repo.add_event.return_value = 101 # event_id
        
        # Create signals spy
        spy = Mock()
        worker.event_saved.connect(spy)
        
        # Prepare task data
        data = {
            'detection': sample_detection,
            'frame': mock_frame,
            'timestamp': time.time()
        }
        
        # Manually invoke processing logic
        worker._handle_event_task(data)
        
        # Assertions
        mock_save_snapshot.assert_called_once()
        worker._event_repo.add_event.assert_called_once()
        args, kwargs = worker._event_repo.add_event.call_args
        assert kwargs['snapshot_path'] == "/path/to/snapshot.jpg"
        assert kwargs['object_label'] == sample_detection.label
        
        spy.assert_called_with(101)

    def test_process_reid_task(self, worker):
        data = {
            'user_id': 5,
            'vector': np.ones((512,)),
            'confidence': 0.9
        }
        
        worker._handle_reid_task(data)
        
        worker._embedding_repo.add_reid_embedding.assert_called_once_with(5, data['vector'], 0.9)

    def test_process_gait_task(self, worker):
        data = {
            'user_id': 7,
            'embedding': np.ones((128,)),
            'confidence': 0.8
        }
        worker._embedding_repo.add_gait_embedding.return_value = 500 # row_id
        
        spy = Mock()
        worker.gait_saved.connect(spy)
        
        worker._handle_gait_task(data)
        
        worker._embedding_repo.add_gait_embedding.assert_called_once_with(7, data['embedding'], 0.8)
        spy.assert_called_with(7, 500)

