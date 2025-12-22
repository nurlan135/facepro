"""
User Repository Unit Tests
Tests for user database operations.
"""

import pytest
from unittest.mock import Mock, patch


class TestUserRepositoryInit:
    """Test UserRepository initialization."""
    
    def test_import_user_repository(self):
        """UserRepository modulu import olunmalı."""
        from src.core.database.repositories.user_repository import UserRepository
        assert UserRepository is not None
    
    def test_create_instance(self):
        """UserRepository instansı yaradılmalı."""
        from src.core.database.repositories.user_repository import UserRepository
        repo = UserRepository()
        assert repo is not None


class TestUserRepositoryMethods:
    """Test UserRepository CRUD methods."""
    
    @pytest.fixture
    def repo(self):
        from src.core.database.repositories.user_repository import UserRepository
        return UserRepository()
    
    def test_create_user_exists(self, repo):
        """create_user metodu mövcud olmalı."""
        assert hasattr(repo, 'create_user')
        assert callable(repo.create_user)
    
    def test_get_user_id_by_name_exists(self, repo):
        """get_user_id_by_name metodu mövcud olmalı."""
        assert hasattr(repo, 'get_user_id_by_name')
        assert callable(repo.get_user_id_by_name)
    
    def test_delete_user_exists(self, repo):
        """delete_user metodu mövcud olmalı."""
        assert hasattr(repo, 'delete_user')
        assert callable(repo.delete_user)
    
    def test_get_users_with_stats_exists(self, repo):
        """get_users_with_stats metodu mövcud olmalı."""
        assert hasattr(repo, 'get_users_with_stats')
        assert callable(repo.get_users_with_stats)
    
    def test_get_users_with_stats_returns_list(self, repo):
        """get_users_with_stats() list qaytarmalı."""
        users = repo.get_users_with_stats()
        assert isinstance(users, list)


class TestEventRepository:
    """Test EventRepository."""
    
    def test_import_event_repository(self):
        """EventRepository modulu import olunmalı."""
        from src.core.database.repositories.event_repository import EventRepository
        assert EventRepository is not None
    
    @pytest.fixture
    def repo(self):
        from src.core.database.repositories.event_repository import EventRepository
        return EventRepository()
    
    def test_add_event_exists(self, repo):
        """add_event metodu mövcud olmalı."""
        assert hasattr(repo, 'add_event')
        assert callable(repo.add_event)


class TestEmbeddingRepository:
    """Test EmbeddingRepository."""
    
    def test_import_embedding_repository(self):
        """EmbeddingRepository modulu import olunmalı."""
        from src.core.database.repositories.embedding_repository import EmbeddingRepository
        assert EmbeddingRepository is not None
    
    @pytest.fixture
    def repo(self):
        from src.core.database.repositories.embedding_repository import EmbeddingRepository
        return EmbeddingRepository()
    
    def test_add_reid_embedding_exists(self, repo):
        """add_reid_embedding metodu mövcud olmalı."""
        assert hasattr(repo, 'add_reid_embedding')
        assert callable(repo.add_reid_embedding)
    
    def test_add_gait_embedding_exists(self, repo):
        """add_gait_embedding metodu mövcud olmalı."""
        assert hasattr(repo, 'add_gait_embedding')
        assert callable(repo.add_gait_embedding)
    
    def test_get_reid_embeddings_exists(self, repo):
        """get_reid_embeddings_with_names metodu mövcud olmalı."""
        assert hasattr(repo, 'get_reid_embeddings_with_names')
        assert callable(repo.get_reid_embeddings_with_names)
    
    def test_get_gait_embeddings_exists(self, repo):
        """get_gait_embeddings_with_names metodu mövcud olmalı."""
        assert hasattr(repo, 'get_gait_embeddings_with_names')
        assert callable(repo.get_gait_embeddings_with_names)


class TestDatabaseManager:
    """Test DatabaseManager."""
    
    def test_import_db_manager(self):
        """DatabaseManager modulu import olunmalı."""
        from src.core.database.db_manager import DatabaseManager
        assert DatabaseManager is not None
    
    def test_singleton_pattern(self):
        """DatabaseManager() həmişə eyni instansı qaytarmalı."""
        from src.core.database.db_manager import DatabaseManager
        
        manager1 = DatabaseManager()
        manager2 = DatabaseManager()
        
        assert manager1 is manager2
    
    def test_get_connection_exists(self):
        """get_connection metodu mövcud olmalı."""
        from src.core.database.db_manager import DatabaseManager
        manager = DatabaseManager()
        assert hasattr(manager, 'get_connection')
        assert callable(manager.get_connection)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
