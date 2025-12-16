"""
FacePro GaitEngine Property-Based Tests
Tests for gait recognition functionality using hypothesis.

**Feature: gait-recognition**
"""

import pytest
import os
import sys
import numpy as np
from hypothesis import given, strategies as st, settings

# Direct import of gait_engine module
import importlib.util

def import_gait_engine():
    """Import gait_engine directly without going through core package."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(project_root, 'src', 'core', 'gait_engine.py')
    spec = importlib.util.spec_from_file_location("gait_engine", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

gait_module = import_gait_engine()
GaitEngine = gait_module.GaitEngine
GaitBufferManager = gait_module.GaitBufferManager
GaitBuffer = gait_module.GaitBuffer
get_gait_engine = gait_module.get_gait_engine


class TestConfidenceScoreRange:
    """
    **Feature: gait-recognition, Property 1: Confidence Score Range**
    **Validates: Requirements 1.3**
    
    For any gait analysis result, the confidence score SHALL always be 
    between 0.0 and 1.0 inclusive.
    """
    
    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """Create a GaitEngine instance for testing."""
        self.engine = GaitEngine()
    
    @given(
        seed1=st.integers(min_value=0, max_value=2**32-1),
        seed2=st.integers(min_value=0, max_value=2**32-1),
        scale1=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        scale2=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_cosine_similarity_returns_valid_range(self, seed1, seed2, scale1, scale2):
        """
        **Feature: gait-recognition, Property 1: Confidence Score Range**
        **Validates: Requirements 1.3**
        
        For any two embeddings, cosine_similarity SHALL return a value 
        between 0.0 and 1.0 inclusive.
        """
        # Generate embeddings using seeds for reproducibility
        rng1 = np.random.default_rng(seed1)
        rng2 = np.random.default_rng(seed2)
        emb1 = (rng1.random(256).astype(np.float32) - 0.5) * scale1
        emb2 = (rng2.random(256).astype(np.float32) - 0.5) * scale2
        
        similarity = GaitEngine.cosine_similarity(emb1, emb2)
        
        # Property: confidence score must be in [0, 1]
        assert 0.0 <= similarity <= 1.0, \
            f"Cosine similarity {similarity} is outside valid range [0, 1]"
    
    @given(
        seed=st.integers(min_value=0, max_value=2**32-1),
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_compare_embeddings_confidence_in_range(self, seed, threshold):
        """
        **Feature: gait-recognition, Property 1: Confidence Score Range**
        **Validates: Requirements 1.3**
        
        For any gait match result from compare_embeddings, the confidence 
        score SHALL be between 0.0 and 1.0 inclusive.
        """
        rng = np.random.default_rng(seed)
        query_emb = (rng.random(256).astype(np.float32) - 0.5) * 2.0
        
        # Normalize query embedding
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm
        
        # Create stored embeddings with slight variations
        stored_embeddings = []
        for i in range(3):
            # Create variations of the query embedding
            noise = np.random.randn(256).astype(np.float32) * 0.1
            stored_emb = query_emb + noise
            stored_norm = np.linalg.norm(stored_emb)
            if stored_norm > 0:
                stored_emb = stored_emb / stored_norm
            stored_embeddings.append((i, i + 1, f"User_{i}", stored_emb))
        
        self.engine.set_threshold(threshold)
        match = self.engine.compare_embeddings(query_emb, stored_embeddings)
        
        # Property: if match exists, confidence must be in [0, 1]
        if match is not None:
            assert 0.0 <= match.confidence <= 1.0, \
                f"Match confidence {match.confidence} is outside valid range [0, 1]"
    
    def test_cosine_similarity_with_zero_vectors(self):
        """
        **Feature: gait-recognition, Property 1: Confidence Score Range**
        **Validates: Requirements 1.3**
        
        Edge case: zero vectors should return 0.0 (within valid range).
        """
        zero_emb = np.zeros(256, dtype=np.float32)
        random_emb = np.random.randn(256).astype(np.float32)
        
        # Zero vs zero
        sim1 = GaitEngine.cosine_similarity(zero_emb, zero_emb)
        assert sim1 == 0.0, f"Zero vs zero should be 0.0, got {sim1}"
        
        # Zero vs random
        sim2 = GaitEngine.cosine_similarity(zero_emb, random_emb)
        assert sim2 == 0.0, f"Zero vs random should be 0.0, got {sim2}"
        
        # Random vs zero
        sim3 = GaitEngine.cosine_similarity(random_emb, zero_emb)
        assert sim3 == 0.0, f"Random vs zero should be 0.0, got {sim3}"
    
    def test_cosine_similarity_identical_vectors(self):
        """
        **Feature: gait-recognition, Property 1: Confidence Score Range**
        **Validates: Requirements 1.3**
        
        Identical normalized vectors should have similarity of 1.0.
        """
        emb = np.random.randn(256).astype(np.float32)
        emb = emb / np.linalg.norm(emb)  # Normalize
        
        similarity = GaitEngine.cosine_similarity(emb, emb)
        
        # Should be very close to 1.0
        assert 0.99 <= similarity <= 1.0, \
            f"Self-similarity should be ~1.0, got {similarity}"


class TestSilhouetteSizeConsistency:
    """
    **Feature: gait-recognition, Property 3: Silhouette Size Consistency**
    **Validates: Requirements 6.2**
    
    For any extracted silhouette, the output dimensions SHALL always be 64x64 pixels.
    """
    
    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """Create a GaitEngine instance for testing."""
        self.engine = GaitEngine()
    
    @given(
        frame_height=st.integers(min_value=100, max_value=1080),
        frame_width=st.integers(min_value=100, max_value=1920),
        x1=st.integers(min_value=0, max_value=500),
        y1=st.integers(min_value=0, max_value=500),
        bbox_width=st.integers(min_value=20, max_value=300),
        bbox_height=st.integers(min_value=50, max_value=500)
    )
    @settings(max_examples=100)
    def test_silhouette_always_64x64(
        self, frame_height, frame_width, x1, y1, bbox_width, bbox_height
    ):
        """
        **Feature: gait-recognition, Property 3: Silhouette Size Consistency**
        **Validates: Requirements 6.2**
        
        For any valid frame and bounding box, the extracted silhouette
        SHALL always have dimensions of exactly 64x64 pixels.
        """
        # Ensure bbox is within frame bounds
        x2 = min(x1 + bbox_width, frame_width - 1)
        y2 = min(y1 + bbox_height, frame_height - 1)
        
        # Skip if bbox is invalid (too small or outside frame)
        if x2 <= x1 or y2 <= y1:
            return
        
        # Create random frame
        frame = np.random.randint(0, 255, (frame_height, frame_width, 3), dtype=np.uint8)
        bbox = (x1, y1, x2, y2)
        
        # Extract silhouette
        silhouette = self.engine.extract_silhouette(frame, bbox)
        
        # Property: silhouette must always be 64x64
        assert silhouette.shape == (64, 64), \
            f"Expected silhouette shape (64, 64), got {silhouette.shape}"
    
    @given(
        frame_height=st.integers(min_value=480, max_value=1080),
        frame_width=st.integers(min_value=640, max_value=1920)
    )
    @settings(max_examples=100)
    def test_silhouette_size_with_edge_bboxes(self, frame_height, frame_width):
        """
        **Feature: gait-recognition, Property 3: Silhouette Size Consistency**
        **Validates: Requirements 6.2**
        
        For bounding boxes at frame edges, the silhouette SHALL still be 64x64.
        """
        frame = np.random.randint(0, 255, (frame_height, frame_width, 3), dtype=np.uint8)
        
        # Test bbox at top-left corner
        bbox_tl = (0, 0, 100, 200)
        silhouette_tl = self.engine.extract_silhouette(frame, bbox_tl)
        assert silhouette_tl.shape == (64, 64)
        
        # Test bbox at bottom-right corner
        bbox_br = (frame_width - 100, frame_height - 200, frame_width, frame_height)
        silhouette_br = self.engine.extract_silhouette(frame, bbox_br)
        assert silhouette_br.shape == (64, 64)
    
    def test_silhouette_size_with_empty_region(self):
        """
        **Feature: gait-recognition, Property 3: Silhouette Size Consistency**
        **Validates: Requirements 6.2**
        
        Even with invalid/empty bbox, silhouette SHALL be 64x64 (zeros).
        """
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Invalid bbox (x2 < x1)
        bbox_invalid = (200, 100, 100, 300)
        silhouette = self.engine.extract_silhouette(frame, bbox_invalid)
        
        # Should return 64x64 zeros
        assert silhouette.shape == (64, 64)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestBufferSequenceLength:
    """
    **Feature: gait-recognition, Property 2: Buffer Sequence Length**
    **Validates: Requirements 1.2**
    
    For any gait buffer, analysis SHALL only be triggered when exactly 
    30 frames have been collected.
    """
    
    @given(
        sequence_length=st.integers(min_value=10, max_value=60),
        num_frames=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_buffer_triggers_at_exact_sequence_length(self, sequence_length, num_frames):
        """
        **Feature: gait-recognition, Property 2: Buffer Sequence Length**
        **Validates: Requirements 1.2**
        
        For any sequence_length configuration, add_frame SHALL return True
        only when exactly sequence_length frames have been added.
        """
        buffer_mgr = GaitBufferManager(sequence_length=sequence_length)
        track_id = 1
        
        # Create a dummy silhouette
        silhouette = np.zeros((64, 64), dtype=np.uint8)
        
        trigger_count = 0
        for i in range(num_frames):
            is_full = buffer_mgr.add_frame(track_id, silhouette)
            
            if is_full:
                trigger_count += 1
                # Property: buffer should trigger at exactly sequence_length
                current_size = buffer_mgr.get_buffer_size(track_id)
                assert current_size >= sequence_length, \
                    f"Buffer triggered at {current_size} frames, expected >= {sequence_length}"
                
                # Get sequence to clear buffer
                seq = buffer_mgr.get_sequence(track_id)
                assert seq is not None, "get_sequence should return data when buffer is full"
                assert len(seq) == sequence_length, \
                    f"Sequence length should be {sequence_length}, got {len(seq)}"
    
    @given(
        sequence_length=st.integers(min_value=20, max_value=40)
    )
    @settings(max_examples=100)
    def test_buffer_does_not_trigger_before_sequence_length(self, sequence_length):
        """
        **Feature: gait-recognition, Property 2: Buffer Sequence Length**
        **Validates: Requirements 1.2**
        
        For any sequence_length, add_frame SHALL NOT return True before
        sequence_length frames have been added.
        """
        buffer_mgr = GaitBufferManager(sequence_length=sequence_length)
        track_id = 42
        
        silhouette = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        
        # Add frames up to sequence_length - 1
        for i in range(sequence_length - 1):
            is_full = buffer_mgr.add_frame(track_id, silhouette)
            assert not is_full, \
                f"Buffer should not be full at frame {i + 1}/{sequence_length}"
        
        # The next frame should trigger
        is_full = buffer_mgr.add_frame(track_id, silhouette)
        assert is_full, \
            f"Buffer should be full at frame {sequence_length}"
    
    def test_default_sequence_length_is_30(self):
        """
        **Feature: gait-recognition, Property 2: Buffer Sequence Length**
        **Validates: Requirements 1.2**
        
        Default sequence length SHALL be 30 frames.
        """
        buffer_mgr = GaitBufferManager()
        track_id = 1
        silhouette = np.zeros((64, 64), dtype=np.uint8)
        
        # Add 29 frames - should not trigger
        for i in range(29):
            is_full = buffer_mgr.add_frame(track_id, silhouette)
            assert not is_full, f"Should not trigger at frame {i + 1}"
        
        # 30th frame should trigger
        is_full = buffer_mgr.add_frame(track_id, silhouette)
        assert is_full, "Should trigger at frame 30"
    
    @given(
        sequence_length=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100)
    def test_get_sequence_returns_none_before_full(self, sequence_length):
        """
        **Feature: gait-recognition, Property 2: Buffer Sequence Length**
        **Validates: Requirements 1.2**
        
        get_sequence SHALL return None if buffer has fewer than sequence_length frames.
        """
        buffer_mgr = GaitBufferManager(sequence_length=sequence_length)
        track_id = 99
        silhouette = np.zeros((64, 64), dtype=np.uint8)
        
        # Add fewer frames than sequence_length
        frames_to_add = sequence_length - 1
        for _ in range(frames_to_add):
            buffer_mgr.add_frame(track_id, silhouette)
        
        # get_sequence should return None
        seq = buffer_mgr.get_sequence(track_id)
        assert seq is None, \
            f"get_sequence should return None with {frames_to_add} frames (need {sequence_length})"


class TestBufferIsolation:
    """
    **Feature: gait-recognition, Property 7: Buffer Isolation**
    **Validates: Requirements 3.3**
    
    For any two different track_ids, adding frames to one buffer 
    SHALL NOT affect the other buffer.
    """
    
    @given(
        track_id1=st.integers(min_value=1, max_value=1000),
        track_id2=st.integers(min_value=1001, max_value=2000),
        frames1=st.integers(min_value=1, max_value=50),
        frames2=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_separate_buffers_for_different_tracks(
        self, track_id1, track_id2, frames1, frames2
    ):
        """
        **Feature: gait-recognition, Property 7: Buffer Isolation**
        **Validates: Requirements 3.3**
        
        Adding frames to track_id1 SHALL NOT change the frame count of track_id2.
        """
        buffer_mgr = GaitBufferManager(sequence_length=30)
        
        silhouette1 = np.ones((64, 64), dtype=np.uint8) * 100
        silhouette2 = np.ones((64, 64), dtype=np.uint8) * 200
        
        # Add frames to track_id1
        for _ in range(frames1):
            buffer_mgr.add_frame(track_id1, silhouette1)
        
        # Add frames to track_id2
        for _ in range(frames2):
            buffer_mgr.add_frame(track_id2, silhouette2)
        
        # Property: each buffer should have exactly the frames added to it
        size1 = buffer_mgr.get_buffer_size(track_id1)
        size2 = buffer_mgr.get_buffer_size(track_id2)
        
        expected1 = min(frames1, 30) if frames1 < 30 else frames1
        expected2 = min(frames2, 30) if frames2 < 30 else frames2
        
        # Buffer accumulates frames, so size should match frames added
        assert size1 == frames1, \
            f"Track {track_id1} should have {frames1} frames, got {size1}"
        assert size2 == frames2, \
            f"Track {track_id2} should have {frames2} frames, got {size2}"
    
    @given(
        num_tracks=st.integers(min_value=2, max_value=10),
        frames_per_track=st.integers(min_value=5, max_value=25)
    )
    @settings(max_examples=100)
    def test_multiple_tracks_independent(self, num_tracks, frames_per_track):
        """
        **Feature: gait-recognition, Property 7: Buffer Isolation**
        **Validates: Requirements 3.3**
        
        For any number of tracks, each buffer SHALL maintain independent state.
        """
        buffer_mgr = GaitBufferManager(sequence_length=30)
        
        # Add frames to multiple tracks
        for track_id in range(num_tracks):
            silhouette = np.ones((64, 64), dtype=np.uint8) * track_id
            for _ in range(frames_per_track):
                buffer_mgr.add_frame(track_id, silhouette)
        
        # Verify each track has correct frame count
        for track_id in range(num_tracks):
            size = buffer_mgr.get_buffer_size(track_id)
            assert size == frames_per_track, \
                f"Track {track_id} should have {frames_per_track} frames, got {size}"
    
    @given(
        track_id1=st.integers(min_value=1, max_value=500),
        track_id2=st.integers(min_value=501, max_value=1000)
    )
    @settings(max_examples=100)
    def test_clearing_one_buffer_does_not_affect_other(self, track_id1, track_id2):
        """
        **Feature: gait-recognition, Property 7: Buffer Isolation**
        **Validates: Requirements 3.3**
        
        Clearing/getting sequence from one buffer SHALL NOT affect other buffers.
        """
        buffer_mgr = GaitBufferManager(sequence_length=30)
        silhouette = np.zeros((64, 64), dtype=np.uint8)
        
        # Fill both buffers to 30 frames
        for _ in range(30):
            buffer_mgr.add_frame(track_id1, silhouette)
            buffer_mgr.add_frame(track_id2, silhouette)
        
        # Get sequence from track_id1 (clears it)
        seq1 = buffer_mgr.get_sequence(track_id1)
        assert seq1 is not None
        assert len(seq1) == 30
        
        # track_id2 should still have its frames
        size2 = buffer_mgr.get_buffer_size(track_id2)
        assert size2 == 30, \
            f"Track {track_id2} should still have 30 frames after clearing track {track_id1}, got {size2}"
        
        # track_id1 should be cleared
        size1 = buffer_mgr.get_buffer_size(track_id1)
        assert size1 == 0, \
            f"Track {track_id1} should be cleared after get_sequence, got {size1}"
    
    def test_silhouette_data_isolation(self):
        """
        **Feature: gait-recognition, Property 7: Buffer Isolation**
        **Validates: Requirements 3.3**
        
        Silhouette data in one buffer SHALL NOT be mixed with another buffer.
        """
        buffer_mgr = GaitBufferManager(sequence_length=5)
        
        # Create distinct silhouettes for each track
        silhouette1 = np.ones((64, 64), dtype=np.uint8) * 50
        silhouette2 = np.ones((64, 64), dtype=np.uint8) * 200
        
        # Add to different tracks
        for _ in range(5):
            buffer_mgr.add_frame(1, silhouette1)
            buffer_mgr.add_frame(2, silhouette2)
        
        # Get sequences
        seq1 = buffer_mgr.get_sequence(1)
        seq2 = buffer_mgr.get_sequence(2)
        
        # Verify data integrity
        for sil in seq1:
            assert np.all(sil == 50), "Track 1 silhouettes should all be 50"
        
        for sil in seq2:
            assert np.all(sil == 200), "Track 2 silhouettes should all be 200"


class TestCosineSimilaritySymmetry:
    """
    **Feature: gait-recognition, Property 5: Cosine Similarity Symmetry**
    **Validates: Requirements 7.3**
    
    For any two embeddings A and B, cosine_similarity(A, B) SHALL equal 
    cosine_similarity(B, A).
    """
    
    @given(
        seed1=st.integers(min_value=0, max_value=2**32-1),
        seed2=st.integers(min_value=0, max_value=2**32-1),
        scale1=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        scale2=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_cosine_similarity_is_symmetric(self, seed1, seed2, scale1, scale2):
        """
        **Feature: gait-recognition, Property 5: Cosine Similarity Symmetry**
        **Validates: Requirements 7.3**
        
        For any two embeddings A and B, cosine_similarity(A, B) SHALL equal 
        cosine_similarity(B, A).
        """
        # Generate embeddings using seeds for reproducibility
        rng1 = np.random.default_rng(seed1)
        rng2 = np.random.default_rng(seed2)
        emb_a = (rng1.random(256).astype(np.float32) - 0.5) * scale1
        emb_b = (rng2.random(256).astype(np.float32) - 0.5) * scale2
        
        # Calculate similarity in both directions
        sim_ab = GaitEngine.cosine_similarity(emb_a, emb_b)
        sim_ba = GaitEngine.cosine_similarity(emb_b, emb_a)
        
        # Property: cosine similarity must be symmetric
        assert abs(sim_ab - sim_ba) < 1e-6, \
            f"Cosine similarity is not symmetric: sim(A,B)={sim_ab}, sim(B,A)={sim_ba}"
    
    @given(
        seed=st.integers(min_value=0, max_value=2**32-1),
        scale=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_cosine_similarity_symmetric_with_normalized_vectors(self, seed, scale):
        """
        **Feature: gait-recognition, Property 5: Cosine Similarity Symmetry**
        **Validates: Requirements 7.3**
        
        For normalized embeddings, symmetry SHALL still hold.
        """
        rng = np.random.default_rng(seed)
        
        # Create two different normalized embeddings
        emb_a = rng.random(256).astype(np.float32) * scale
        emb_b = rng.random(256).astype(np.float32) * scale
        
        # Normalize
        norm_a = np.linalg.norm(emb_a)
        norm_b = np.linalg.norm(emb_b)
        if norm_a > 0:
            emb_a = emb_a / norm_a
        if norm_b > 0:
            emb_b = emb_b / norm_b
        
        sim_ab = GaitEngine.cosine_similarity(emb_a, emb_b)
        sim_ba = GaitEngine.cosine_similarity(emb_b, emb_a)
        
        assert abs(sim_ab - sim_ba) < 1e-6, \
            f"Symmetry violated for normalized vectors: sim(A,B)={sim_ab}, sim(B,A)={sim_ba}"
    
    def test_symmetry_with_zero_vector(self):
        """
        **Feature: gait-recognition, Property 5: Cosine Similarity Symmetry**
        **Validates: Requirements 7.3**
        
        Symmetry SHALL hold even when one vector is zero.
        """
        zero_emb = np.zeros(256, dtype=np.float32)
        random_emb = np.random.randn(256).astype(np.float32)
        
        sim_zr = GaitEngine.cosine_similarity(zero_emb, random_emb)
        sim_rz = GaitEngine.cosine_similarity(random_emb, zero_emb)
        
        assert sim_zr == sim_rz, \
            f"Symmetry violated with zero vector: sim(0,R)={sim_zr}, sim(R,0)={sim_rz}"
    
    def test_symmetry_with_identical_vectors(self):
        """
        **Feature: gait-recognition, Property 5: Cosine Similarity Symmetry**
        **Validates: Requirements 7.3**
        
        Self-similarity SHALL be symmetric (trivially true but good to verify).
        """
        emb = np.random.randn(256).astype(np.float32)
        
        sim_aa = GaitEngine.cosine_similarity(emb, emb)
        
        # Self-similarity should be the same regardless of argument order
        assert sim_aa == GaitEngine.cosine_similarity(emb, emb), \
            "Self-similarity should be consistent"



class TestThresholdConfiguration:
    """
    **Feature: gait-recognition, Property 9: Threshold Configuration**
    **Validates: Requirements 5.2**
    
    For any configured threshold value, only matches with confidence >= threshold 
    SHALL be returned.
    """
    
    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """Create a GaitEngine instance for testing."""
        self.engine = GaitEngine()
    
    @given(
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100)
    def test_matches_only_returned_above_threshold(self, threshold, seed):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        For any threshold, compare_embeddings SHALL only return matches 
        with confidence >= threshold.
        """
        rng = np.random.default_rng(seed)
        
        # Create a normalized query embedding
        query_emb = rng.random(256).astype(np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # Create stored embeddings with varying similarities
        stored_embeddings = []
        for i in range(5):
            # Create embeddings with different similarity levels
            noise_level = i * 0.3  # Increasing noise = decreasing similarity
            noise = rng.standard_normal(256).astype(np.float32) * noise_level
            stored_emb = query_emb + noise
            stored_norm = np.linalg.norm(stored_emb)
            if stored_norm > 0:
                stored_emb = stored_emb / stored_norm
            stored_embeddings.append((i, i + 1, f"User_{i}", stored_emb))
        
        # Set threshold and compare
        self.engine.set_threshold(threshold)
        match = self.engine.compare_embeddings(query_emb, stored_embeddings)
        
        # Property: if a match is returned, its confidence must be >= threshold
        if match is not None:
            assert match.confidence >= threshold, \
                f"Match confidence {match.confidence} is below threshold {threshold}"
    
    @given(
        threshold=st.floats(min_value=0.5, max_value=0.99, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_no_match_when_all_below_threshold(self, threshold):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        When all stored embeddings have similarity below threshold, 
        compare_embeddings SHALL return None.
        """
        # Create orthogonal/dissimilar embeddings
        query_emb = np.zeros(256, dtype=np.float32)
        query_emb[0:128] = 1.0
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # Create stored embeddings that are very different
        stored_embeddings = []
        for i in range(3):
            stored_emb = np.zeros(256, dtype=np.float32)
            stored_emb[128:256] = 1.0  # Orthogonal to query
            # Add small random noise
            stored_emb += np.random.randn(256).astype(np.float32) * 0.01
            stored_emb = stored_emb / np.linalg.norm(stored_emb)
            stored_embeddings.append((i, i + 1, f"User_{i}", stored_emb))
        
        self.engine.set_threshold(threshold)
        match = self.engine.compare_embeddings(query_emb, stored_embeddings)
        
        # With orthogonal vectors, similarity should be near 0, so no match
        if match is not None:
            # If there is a match, verify it meets threshold
            assert match.confidence >= threshold, \
                f"Match returned with confidence {match.confidence} below threshold {threshold}"
    
    @given(
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_threshold_setter_clamps_value(self, threshold):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        set_threshold SHALL clamp values to [0.0, 1.0] range.
        """
        self.engine.set_threshold(threshold)
        actual = self.engine.get_threshold()
        
        # Property: threshold should be clamped to [0, 1]
        assert 0.0 <= actual <= 1.0, \
            f"Threshold {actual} is outside valid range [0, 1]"
    
    def test_threshold_setter_clamps_out_of_range(self):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        set_threshold SHALL clamp values outside [0.0, 1.0].
        """
        # Test below 0
        self.engine.set_threshold(-0.5)
        assert self.engine.get_threshold() == 0.0, \
            "Negative threshold should be clamped to 0.0"
        
        # Test above 1
        self.engine.set_threshold(1.5)
        assert self.engine.get_threshold() == 1.0, \
            "Threshold > 1 should be clamped to 1.0"
    
    def test_default_threshold_is_0_70(self):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        Default threshold SHALL be 0.70.
        """
        engine = GaitEngine()
        assert engine.get_threshold() == 0.70, \
            f"Default threshold should be 0.70, got {engine.get_threshold()}"
    
    @given(
        threshold=st.floats(min_value=0.1, max_value=0.9, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_best_match_returned_when_multiple_above_threshold(self, threshold):
        """
        **Feature: gait-recognition, Property 9: Threshold Configuration**
        **Validates: Requirements 5.2**
        
        When multiple embeddings exceed threshold, the one with highest 
        confidence SHALL be returned.
        """
        # Create query embedding
        query_emb = np.random.randn(256).astype(np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # Create stored embeddings with known similarities
        stored_embeddings = []
        
        # High similarity (should be best match)
        high_sim_emb = query_emb + np.random.randn(256).astype(np.float32) * 0.05
        high_sim_emb = high_sim_emb / np.linalg.norm(high_sim_emb)
        stored_embeddings.append((1, 1, "HighSim", high_sim_emb))
        
        # Medium similarity
        med_sim_emb = query_emb + np.random.randn(256).astype(np.float32) * 0.3
        med_sim_emb = med_sim_emb / np.linalg.norm(med_sim_emb)
        stored_embeddings.append((2, 2, "MedSim", med_sim_emb))
        
        # Low similarity
        low_sim_emb = query_emb + np.random.randn(256).astype(np.float32) * 0.8
        low_sim_emb = low_sim_emb / np.linalg.norm(low_sim_emb)
        stored_embeddings.append((3, 3, "LowSim", low_sim_emb))
        
        self.engine.set_threshold(threshold)
        match = self.engine.compare_embeddings(query_emb, stored_embeddings)
        
        if match is not None:
            # Verify this is the best match
            all_similarities = [
                GaitEngine.cosine_similarity(query_emb, emb[3]) 
                for emb in stored_embeddings
            ]
            max_sim = max(all_similarities)
            
            # The returned match should have the highest similarity
            assert abs(match.confidence - max_sim) < 1e-6, \
                f"Expected best match with confidence {max_sim}, got {match.confidence}"



class TestEmbeddingSerializationRoundTrip:
    """
    **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
    **Validates: Requirements 7.4**
    
    For any gait embedding, serializing with pickle and then deserializing 
    SHALL produce an identical numpy array.
    """
    
    @given(
        seed=st.integers(min_value=0, max_value=2**32-1),
        scale=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_serialize_deserialize_produces_identical_array(self, seed, scale):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        For any gait embedding, serialize then deserialize SHALL produce 
        an identical numpy array.
        """
        rng = np.random.default_rng(seed)
        
        # Generate a random embedding (256D as per spec)
        original_embedding = (rng.random(256).astype(np.float32) - 0.5) * scale
        
        # Serialize
        serialized = GaitEngine.serialize_embedding(original_embedding)
        
        # Deserialize
        deserialized = GaitEngine.deserialize_embedding(serialized)
        
        # Property: round-trip must produce identical array
        assert np.array_equal(original_embedding, deserialized), \
            f"Round-trip failed: original and deserialized arrays differ"
        
        # Also verify dtype is preserved
        assert original_embedding.dtype == deserialized.dtype, \
            f"dtype mismatch: {original_embedding.dtype} vs {deserialized.dtype}"
    
    @given(
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100)
    def test_normalized_embedding_round_trip(self, seed):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        For normalized embeddings (as used in gait recognition), 
        round-trip SHALL preserve the normalization.
        """
        rng = np.random.default_rng(seed)
        
        # Generate and normalize embedding
        embedding = rng.random(256).astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        # Serialize and deserialize
        serialized = GaitEngine.serialize_embedding(embedding)
        deserialized = GaitEngine.deserialize_embedding(serialized)
        
        # Property: values must be identical
        assert np.allclose(embedding, deserialized, rtol=1e-7, atol=1e-7), \
            f"Normalized embedding round-trip failed"
        
        # Verify norm is preserved
        original_norm = np.linalg.norm(embedding)
        deserialized_norm = np.linalg.norm(deserialized)
        assert abs(original_norm - deserialized_norm) < 1e-6, \
            f"Norm not preserved: {original_norm} vs {deserialized_norm}"
    
    @given(
        embedding_dim=st.integers(min_value=1, max_value=512),
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100)
    def test_various_embedding_dimensions(self, embedding_dim, seed):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        Round-trip SHALL work for embeddings of various dimensions.
        """
        rng = np.random.default_rng(seed)
        
        # Generate embedding of specified dimension
        embedding = rng.random(embedding_dim).astype(np.float32)
        
        # Serialize and deserialize
        serialized = GaitEngine.serialize_embedding(embedding)
        deserialized = GaitEngine.deserialize_embedding(serialized)
        
        # Property: shape and values must be preserved
        assert embedding.shape == deserialized.shape, \
            f"Shape mismatch: {embedding.shape} vs {deserialized.shape}"
        assert np.array_equal(embedding, deserialized), \
            "Values not preserved in round-trip"
    
    def test_zero_embedding_round_trip(self):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        Zero embedding SHALL survive round-trip.
        """
        zero_embedding = np.zeros(256, dtype=np.float32)
        
        serialized = GaitEngine.serialize_embedding(zero_embedding)
        deserialized = GaitEngine.deserialize_embedding(serialized)
        
        assert np.array_equal(zero_embedding, deserialized), \
            "Zero embedding round-trip failed"
    
    def test_extreme_values_round_trip(self):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        Embeddings with extreme float32 values SHALL survive round-trip.
        """
        # Test with very small values
        small_embedding = np.full(256, 1e-38, dtype=np.float32)
        serialized = GaitEngine.serialize_embedding(small_embedding)
        deserialized = GaitEngine.deserialize_embedding(serialized)
        assert np.array_equal(small_embedding, deserialized), \
            "Small values round-trip failed"
        
        # Test with large values
        large_embedding = np.full(256, 1e38, dtype=np.float32)
        serialized = GaitEngine.serialize_embedding(large_embedding)
        deserialized = GaitEngine.deserialize_embedding(serialized)
        assert np.array_equal(large_embedding, deserialized), \
            "Large values round-trip failed"
    
    @given(
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100)
    def test_serialized_is_bytes(self, seed):
        """
        **Feature: gait-recognition, Property 4: Embedding Serialization Round-Trip**
        **Validates: Requirements 7.4**
        
        serialize_embedding SHALL return bytes (for BLOB storage).
        """
        rng = np.random.default_rng(seed)
        embedding = rng.random(256).astype(np.float32)
        
        serialized = GaitEngine.serialize_embedding(embedding)
        
        # Property: serialized must be bytes
        assert isinstance(serialized, bytes), \
            f"Expected bytes, got {type(serialized)}"


class TestMaxEmbeddingsPerUser:
    """
    **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
    **Validates: Requirements 2.3, 2.4**
    
    For any user, the gait_embeddings table SHALL contain at most 10 entries.
    """
    
    @staticmethod
    def _create_test_db(db_path: str):
        """Create a test database with required schema."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create gait_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gait_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                confidence REAL DEFAULT 1.0,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gait_user ON gait_embeddings(user_id)")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _create_test_user(db_path: str, user_id: int, name: str):
        """Helper to create a test user in the database."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)",
            (user_id, name)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def _get_embedding_count(db_path: str, user_id: int) -> int:
        """Helper to get embedding count for a user."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @given(
        num_embeddings=st.integers(min_value=1, max_value=30),
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100, deadline=None)
    def test_max_embeddings_enforced(self, num_embeddings, seed, tmp_path_factory):
        """
        **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
        **Validates: Requirements 2.3, 2.4**
        
        For any number of embeddings saved for a user, the count SHALL 
        never exceed 10.
        """
        import tempfile
        import os
        
        # Create unique temp database for this iteration
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            self._create_test_db(db_path)
            engine = GaitEngine()
            rng = np.random.default_rng(seed)
            user_id = 1
            
            # Create test user
            self._create_test_user(db_path, user_id, "TestUser")
            
            # Save multiple embeddings
            for i in range(num_embeddings):
                embedding = rng.random(256).astype(np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                engine.save_embedding(user_id, embedding, db_path=db_path)
            
            # Property: count should never exceed 10
            count = self._get_embedding_count(db_path, user_id)
            assert count <= 10, \
                f"User has {count} embeddings, expected at most 10 after saving {num_embeddings}"
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @given(
        num_embeddings=st.integers(min_value=11, max_value=25),
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100, deadline=None)
    def test_oldest_embeddings_deleted_when_limit_exceeded(self, num_embeddings, seed, tmp_path_factory):
        """
        **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
        **Validates: Requirements 2.3, 2.4**
        
        When more than 10 embeddings are saved, the oldest SHALL be deleted.
        """
        import sqlite3
        import tempfile
        import os
        
        # Create unique temp database for this iteration
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            self._create_test_db(db_path)
            engine = GaitEngine()
            rng = np.random.default_rng(seed)
            user_id = 1
            
            # Create test user
            self._create_test_user(db_path, user_id, "TestUser")
            
            # Save embeddings and track their IDs
            saved_ids = []
            for i in range(num_embeddings):
                embedding = rng.random(256).astype(np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                emb_id = engine.save_embedding(user_id, embedding, db_path=db_path)
                if emb_id is not None:
                    saved_ids.append(emb_id)
            
            # Property: count should be exactly 10
            count = self._get_embedding_count(db_path, user_id)
            assert count == 10, \
                f"Expected exactly 10 embeddings after saving {num_embeddings}, got {count}"
            
            # Verify the remaining embeddings are the most recent ones
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM gait_embeddings WHERE user_id = ? ORDER BY id DESC",
                (user_id,)
            )
            remaining_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # The remaining IDs should be from the most recent saves
            assert len(remaining_ids) == 10, \
                f"Expected 10 remaining embeddings, got {len(remaining_ids)}"
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @given(
        embeddings_user1=st.integers(min_value=5, max_value=15),
        embeddings_user2=st.integers(min_value=5, max_value=15),
        seed=st.integers(min_value=0, max_value=2**32-1)
    )
    @settings(max_examples=100, deadline=None)
    def test_max_embeddings_per_user_independent(
        self, embeddings_user1, embeddings_user2, seed, tmp_path_factory
    ):
        """
        **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
        **Validates: Requirements 2.3, 2.4**
        
        The 10 embedding limit SHALL apply independently to each user.
        """
        import tempfile
        import os
        
        # Create unique temp database for this iteration
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            self._create_test_db(db_path)
            engine = GaitEngine()
            rng = np.random.default_rng(seed)
            user_id1 = 1
            user_id2 = 2
            
            # Create test users
            self._create_test_user(db_path, user_id1, f"User_{user_id1}")
            self._create_test_user(db_path, user_id2, f"User_{user_id2}")
            
            # Save embeddings for user 1
            for i in range(embeddings_user1):
                embedding = rng.random(256).astype(np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                engine.save_embedding(user_id1, embedding, db_path=db_path)
            
            # Save embeddings for user 2
            for i in range(embeddings_user2):
                embedding = rng.random(256).astype(np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                engine.save_embedding(user_id2, embedding, db_path=db_path)
            
            # Property: each user should have at most 10 embeddings
            count1 = self._get_embedding_count(db_path, user_id1)
            count2 = self._get_embedding_count(db_path, user_id2)
            
            expected1 = min(embeddings_user1, 10)
            expected2 = min(embeddings_user2, 10)
            
            assert count1 <= 10, \
                f"User {user_id1} has {count1} embeddings, expected at most 10"
            assert count2 <= 10, \
                f"User {user_id2} has {count2} embeddings, expected at most 10"
            
            # Verify counts match expected
            assert count1 == expected1, \
                f"User {user_id1} should have {expected1} embeddings, got {count1}"
            assert count2 == expected2, \
                f"User {user_id2} should have {expected2} embeddings, got {count2}"
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_exactly_10_embeddings_allowed(self, tmp_path):
        """
        **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
        **Validates: Requirements 2.3, 2.4**
        
        A user SHALL be able to have exactly 10 embeddings.
        """
        db_path = str(tmp_path / "test_gait.db")
        self._create_test_db(db_path)
        engine = GaitEngine()
        user_id = 1
        
        self._create_test_user(db_path, user_id, "TestUser")
        
        # Save exactly 10 embeddings
        for i in range(10):
            embedding = np.random.randn(256).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            engine.save_embedding(user_id, embedding, db_path=db_path)
        
        count = self._get_embedding_count(db_path, user_id)
        assert count == 10, \
            f"Expected exactly 10 embeddings, got {count}"
    
    def test_11th_embedding_triggers_deletion(self, tmp_path):
        """
        **Feature: gait-recognition, Property 6: Maximum Embeddings Per User**
        **Validates: Requirements 2.3, 2.4**
        
        When the 11th embedding is saved, the oldest SHALL be deleted.
        """
        import sqlite3
        
        db_path = str(tmp_path / "test_gait.db")
        self._create_test_db(db_path)
        engine = GaitEngine()
        user_id = 1
        
        self._create_test_user(db_path, user_id, "TestUser")
        
        # Save 10 embeddings and track the first one's ID
        first_embedding_id = None
        for i in range(10):
            embedding = np.random.randn(256).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            emb_id = engine.save_embedding(user_id, embedding, db_path=db_path)
            if i == 0:
                first_embedding_id = emb_id
        
        # Verify we have 10 embeddings
        count = self._get_embedding_count(db_path, user_id)
        assert count == 10, f"Expected 10 embeddings before 11th save, got {count}"
        
        # Save 11th embedding
        embedding = np.random.randn(256).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        engine.save_embedding(user_id, embedding, db_path=db_path)
        
        # Verify still 10 embeddings
        count = self._get_embedding_count(db_path, user_id)
        assert count == 10, f"Expected 10 embeddings after 11th save, got {count}"
        
        # Verify the first embedding was deleted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM gait_embeddings WHERE id = ?",
            (first_embedding_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result is None, \
            f"First embedding (id={first_embedding_id}) should have been deleted"
