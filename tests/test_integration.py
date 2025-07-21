import os
import tempfile
from pathlib import Path
import pytest

from homepy.home import Home
from homepy.resources.symlink import SymlinkResource


class TestSymlinkIntegration:
    """Integration tests for SymlinkResource using temporary directories."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_home:
            with tempfile.TemporaryDirectory() as temp_source:
                # Set HOME environment variable
                original_home = os.environ.get("HOME")
                os.environ["HOME"] = temp_home
                
                yield {
                    "home": Path(temp_home),
                    "source": Path(temp_source)
                }
                
                # Restore original HOME
                if original_home:
                    os.environ["HOME"] = original_home
                elif "HOME" in os.environ:
                    del os.environ["HOME"]

    def test_create_simple_file_symlink(self, temp_dirs):
        """Test creating a simple file symlink."""
        source_file = temp_dirs["source"] / "config.txt"
        target_file = temp_dirs["home"] / ".config" / "myapp" / "config.txt"
        
        # Create source file
        source_file.write_text("test config content")
        
        # Create symlink
        resource = SymlinkResource(source_file, Path(".config/myapp/config.txt"))
        resource.generate()
        
        # Verify symlink was created
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file
        assert target_file.read_text() == "test config content"

    def test_create_directory_symlink(self, temp_dirs):
        """Test creating a directory symlink."""
        source_dir = temp_dirs["source"] / "myproject"
        target_dir = temp_dirs["home"] / "projects" / "myproject"
        
        # Create source directory with files
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        
        # Create symlink
        resource = SymlinkResource(source_dir, Path("projects/myproject"))
        resource.generate()
        
        # Verify directory symlink was created
        assert target_dir.is_symlink()
        assert target_dir.resolve() == source_dir
        assert (target_dir / "file1.txt").read_text() == "content1"
        assert (target_dir / "file2.txt").read_text() == "content2"

    def test_skip_when_source_missing(self, temp_dirs):
        """Test that symlink creation is skipped when source doesn't exist."""
        source_file = temp_dirs["source"] / "nonexistent.txt"
        target_file = temp_dirs["home"] / ".config" / "nonexistent.txt"
        
        # Try to create symlink without source
        resource = SymlinkResource(source_file, Path(".config/nonexistent.txt"))
        resource.generate()
        
        # Verify symlink was not created
        assert not target_file.exists()

    def test_create_parent_directories(self, temp_dirs):
        """Test that parent directories are created when needed."""
        source_file = temp_dirs["source"] / "deep_config.txt"
        target_file = temp_dirs["home"] / ".config" / "app" / "sub" / "deep_config.txt"
        
        # Create source file
        source_file.write_text("deep config")
        
        # Create symlink in nested path
        resource = SymlinkResource(source_file, Path(".config/app/sub/deep_config.txt"))
        resource.generate()
        
        # Verify symlink and parent directories were created
        assert target_file.is_symlink()
        assert target_file.read_text() == "deep config"
        assert target_file.parent.exists()

    def test_skip_existing_correct_symlink(self, temp_dirs):
        """Test that existing correct symlinks are skipped."""
        source_file = temp_dirs["source"] / "existing.txt"
        target_file = temp_dirs["home"] / ".config" / "existing.txt"
        
        # Create source file
        source_file.write_text("existing content")
        
        # Create initial symlink manually
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.symlink_to(source_file)
        
        # Try to create symlink again
        resource = SymlinkResource(source_file, Path(".config/existing.txt"))
        resource.generate()
        
        # Verify symlink still exists and points to correct target
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file

    def test_force_overwrite_wrong_symlink(self, temp_dirs):
        """Test force overwriting a symlink pointing to wrong target."""
        source_file = temp_dirs["source"] / "correct.txt"
        wrong_source = temp_dirs["source"] / "wrong.txt"
        target_file = temp_dirs["home"] / ".config" / "force_test.txt"
        
        # Create source files
        source_file.write_text("correct content")
        wrong_source.write_text("wrong content")
        
        # Create symlink to wrong target
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.symlink_to(wrong_source)
        
        # Force overwrite with correct target
        resource = SymlinkResource(source_file, Path(".config/force_test.txt"), force=True)
        resource.generate()
        
        # Verify symlink now points to correct target
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file
        assert target_file.read_text() == "correct content"

    def test_skip_wrong_symlink_without_force(self, temp_dirs):
        """Test skipping wrong symlink without force flag."""
        source_file = temp_dirs["source"] / "correct.txt"
        wrong_source = temp_dirs["source"] / "wrong.txt"
        target_file = temp_dirs["home"] / ".config" / "skip_test.txt"
        
        # Create source files
        source_file.write_text("correct content")
        wrong_source.write_text("wrong content")
        
        # Create symlink to wrong target
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.symlink_to(wrong_source)
        
        # Try to create symlink without force
        resource = SymlinkResource(source_file, Path(".config/skip_test.txt"), force=False)
        resource.generate()
        
        # Verify symlink still points to wrong target
        assert target_file.is_symlink()
        assert target_file.resolve() == wrong_source


    def test_skip_different_file_without_force(self, temp_dirs):
        """Test skipping different file without force flag."""
        source_file = temp_dirs["source"] / "different.txt"
        target_file = temp_dirs["home"] / ".config" / "different.txt"
        
        # Create source file and different target file
        source_file.write_text("source content")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("target content")
        
        # Try to create symlink without force
        resource = SymlinkResource(source_file, Path(".config/different.txt"), force=False)
        resource.generate()
        
        # Verify file was not replaced
        assert not target_file.is_symlink()
        assert target_file.read_text() == "target content"

    def test_force_overwrite_different_file(self, temp_dirs):
        """Test force overwriting a different file."""
        source_file = temp_dirs["source"] / "force_different.txt"
        target_file = temp_dirs["home"] / ".config" / "force_different.txt"
        
        # Create source file and different target file
        source_file.write_text("source content")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("target content")
        
        # Force create symlink
        resource = SymlinkResource(source_file, Path(".config/force_different.txt"), force=True)
        resource.generate()
        
        # Verify file was replaced with symlink
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file
        assert target_file.read_text() == "source content"

    def test_home_integration(self, temp_dirs):
        """Test integration with Home class."""
        source_file = temp_dirs["source"] / "home_test.txt"
        target_file = temp_dirs["home"] / ".config" / "home_test.txt"
        
        # Create source file
        source_file.write_text("home integration test")
        
        # Create Home instance with symlink resource
        home = Home()
        home.resources.append(SymlinkResource(source_file, Path(".config/home_test.txt")))
        
        # Generate all resources
        home.generate()
        
        # Verify symlink was created
        assert target_file.is_symlink()
        assert target_file.read_text() == "home integration test"

    def test_broken_symlink_handling(self, temp_dirs):
        """Test handling of a broken symlink as target."""
        source_file = temp_dirs["source"] / "real.txt"
        target_file = temp_dirs["home"] / ".config" / "broken.txt"
        source_file.write_text("real content")
        # Create a broken symlink (points to a non-existent file)
        broken_target = temp_dirs["source"] / "does_not_exist.txt"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.symlink_to(broken_target)
        # Try to create symlink without force
        resource = SymlinkResource(source_file, Path(".config/broken.txt"), force=False)
        resource.generate()
        # Should still be a symlink to the broken target
        assert target_file.is_symlink()
        assert Path(os.readlink(target_file)) == broken_target
        # Now try with force
        resource = SymlinkResource(source_file, Path(".config/broken.txt"), force=True)
        resource.generate()
        # Should now be a symlink to the correct source
        assert target_file.is_symlink()
        assert target_file.resolve() == source_file

    def test_skip_existing_correct_directory_symlink(self, temp_dirs):
        """Test that existing correct directory symlinks are skipped if contents are identical."""
        source_dir = temp_dirs["source"] / "dir_symlink"
        target_dir = temp_dirs["home"] / ".config" / "dir_symlink"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        # Create initial symlink manually
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        target_dir.symlink_to(source_dir)
        # Try to create symlink again
        resource = SymlinkResource(source_dir, Path(".config/dir_symlink"))
        resource.generate()
        # Verify symlink still exists and points to correct target
        assert target_dir.is_symlink()
        assert target_dir.resolve() == source_dir
        assert (target_dir / "file.txt").read_text() == "content"

